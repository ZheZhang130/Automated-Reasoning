"""Host-side client for the csc2108 judge container (standard library only).

    from judgekit import Judge
    judge = Judge.public()                       # starts judge-public if needed
    result = judge.run("lcb-atcoder-abc393_a", code)

See timeline/judge_1114.md for the result schema. Requires a running Docker engine
(Docker Desktop, OrbStack or Colima).
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path

__all__ = ["Judge", "JudgeError", "IMAGE", "JUDGE_VERSION"]

JUDGE_VERSION = "0.2.1"
IMAGE = os.environ.get("JUDGE_IMAGE", f"csc2108-judge:{JUDGE_VERSION}")
EVAL_ROOT = Path(__file__).resolve().parent.parent
SUITES = ("public", "hidden")
NPROC_PER_SLOT = 4      # must match NPROC_LIMIT in container/judge.py


class JudgeError(RuntimeError):
    """The judge container could not be started, loaded or queried."""


def docker_bin():
    found = shutil.which("docker")
    if found:
        return found
    orbstack = Path.home() / ".orbstack" / "bin" / "docker"
    if orbstack.exists():
        return str(orbstack)
    raise JudgeError("docker CLI not found. Install Docker Desktop, OrbStack or Colima "
                     "and make sure the engine is running.")


def container_flags(cpus):
    """Fixed flags for every judge container. Same for the public and hidden instances."""
    caps = ["SETUID", "SETGID", "KILL", "CHOWN", "FOWNER", "DAC_OVERRIDE"]
    flags = ["--init", "--network", "none", "--read-only",
             "--tmpfs", "/tmp:rw,mode=711,size=1g",
             "--tmpfs", "/var/judge:rw,mode=700,size=1g",
             "--cpus", str(cpus), "--memory", f"{cpus * 1280 + 1024}m",
             "--pids-limit", str(cpus * NPROC_PER_SLOT + 128),
             "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
             "-e", f"JUDGE_SLOTS={cpus}"]
    for cap in caps:
        flags += ["--cap-add", cap]
    return flags


class Judge:
    def __init__(self, suite="public", *, name=None, image=IMAGE, cpus=4,
                 root=EVAL_ROOT, tasks=None):
        if suite not in SUITES:
            raise ValueError(f"suite must be one of {SUITES}")
        self.suite, self.image, self.cpus = suite, image, int(cpus)
        self.root = Path(root)
        self.tasks = sorted(tasks) if tasks is not None else None
        self.name = name or f"csc2108-judge-{suite}"
        self.docker = docker_bin()

    # ------------------------------------------------------------ lifecycle
    @classmethod
    def public(cls, **kwargs):
        judge = cls("public", **kwargs)
        judge.up()
        return judge

    @classmethod
    def hidden(cls, **kwargs):
        judge = cls("hidden", **kwargs)
        judge.up()
        return judge

    def _call(self, *args, stdin=None, timeout=120):
        try:
            return subprocess.run([self.docker, *args], input=stdin, capture_output=True,
                                  timeout=timeout)
        except OSError as error:  # e.g. the docker binary disappeared
            raise JudgeError(f"cannot run docker: {error}") from error

    def _image_id(self):
        proc = self._call("image", "inspect", "-f", "{{.Id}}", self.image)
        if proc.returncode != 0:
            raise JudgeError(f"image {self.image} not found; build it with judge/setup.sh")
        return proc.stdout.decode().strip()

    def _container_image_id(self):
        """Image ID of the running container, or None if it is not running."""
        proc = self._call("inspect", "-f", "{{.State.Running}} {{.Image}}", self.name)
        if proc.returncode != 0:
            return None
        running, image_id = proc.stdout.decode().split()
        return image_id if running == "true" else None

    def fingerprint(self, archive):
        """Identity of what would be loaded: suite, container settings and test bytes."""
        digest = hashlib.sha256(f"{self.suite}\0{self.cpus}\0".encode())
        digest.update(archive)
        return digest.hexdigest()

    def up(self, force=False):
        """Start the container and load the suite, or reuse a container that runs the
        same image ID with the same fingerprint. Returns `info()`."""
        archive = self._suite_archive()
        fingerprint = self.fingerprint(archive)
        image_id = self._image_id()
        if not force and self._container_image_id() == image_id:
            try:
                info = self.info()
                if info.get("fingerprint") == fingerprint:
                    return info
            except JudgeError:
                pass
        self.down()
        proc = self._call("run", "-d", "--name", self.name,
                          "--label", f"csc2108.judge.suite={self.suite}",
                          *container_flags(self.cpus), image_id, "sleep", "infinity")
        if proc.returncode != 0:
            raise JudgeError(f"docker run failed: {proc.stderr.decode().strip()}")
        self.load(archive, fingerprint)
        return self.info()

    def down(self):
        self._call("rm", "-f", self.name)

    def load(self, archive=None, fingerprint=None):
        """Stream the suite's tests into the container (no bind mount)."""
        archive = archive if archive is not None else self._suite_archive()
        fingerprint = fingerprint or self.fingerprint(archive)
        proc = self._call("exec", "-i", "-u", "0", self.name, "judge", "load",
                          "--suite", self.suite, "--fingerprint", fingerprint,
                          stdin=archive, timeout=600)
        if proc.returncode != 0:
            raise JudgeError(f"judge load failed: {proc.stderr.decode().strip()}")

    def _task_ids(self):
        tasks_dir = self.root / "tasks"
        available = sorted(p.name for p in tasks_dir.iterdir() if (p / "task.json").exists())
        if self.tasks is None:
            return available
        missing = sorted(set(self.tasks) - set(available))
        if missing:
            raise JudgeError(f"unknown tasks: {missing}")
        return self.tasks

    def _suite_archive(self):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w") as archive:
            for task_id in self._task_ids():
                meta = json.loads((self.root / "tasks" / task_id / "task.json").read_text())
                tests = (self.root / "tasks" / task_id / "tests" / "public"
                         if self.suite == "public" else self.root / "hidden" / task_id)
                if not tests.is_dir():
                    raise JudgeError(f"no {self.suite} tests for {task_id} at {tests}")
                for path in sorted(tests.iterdir()):
                    if path.suffix in (".in", ".out"):
                        _add_bytes(archive, f"{task_id}/{path.name}", path.read_bytes())
                _add_bytes(archive, f"{task_id}/task.json",
                           json.dumps({"time_limit_s": meta.get("time_limit_s", 6.0)}).encode())
        return buffer.getvalue()

    # ------------------------------------------------------------ queries
    def _json(self, *args, stdin=None, timeout=120):
        proc = self._call("exec", "-i", self.name, "judge", *args, stdin=stdin, timeout=timeout)
        try:
            return proc.returncode, json.loads(proc.stdout.decode())
        except ValueError:
            return proc.returncode, None if not proc.stderr else {"error": proc.stderr.decode().strip()}

    def info(self):
        code, data = self._json("info")
        if code != 0 or not data or "suite" not in data:
            raise JudgeError(f"judge info failed: {(data or {}).get('error', 'no output')}")
        return data

    def run(self, task_id, code, time_limit=None, timeout=3600):
        """Judge `code` (str or bytes) on one task. Always returns a result dict.

        A judge-side failure is retried once and then returned with
        status "infrastructure_error".
        """
        source = code.encode() if isinstance(code, str) else bytes(code)
        args = ["run", "--task", task_id]
        if time_limit is not None:
            args += ["--time-limit", str(time_limit)]
        last = None
        for _ in range(2):
            try:
                status, data = self._json(*args, stdin=source, timeout=timeout)
            except subprocess.TimeoutExpired:
                status, data = -1, {"error": f"no result within {timeout} s"}
            except JudgeError as error:  # docker could not be run at all
                status, data = -1, {"error": str(error)}
            if status == 0 and data and "status" in data:
                return data
            last = data
        if last and last.get("status") == "infrastructure_error":
            return last
        error = (last or {}).get("error", "judge produced no result")
        return {"judge_version": None, "suite": self.suite, "task_id": task_id,
                "code_sha256": hashlib.sha256(source).hexdigest(),
                "status": "infrastructure_error", "passed": 0, "total": 0,
                "verdict_counts": {}, "cases": [], "first_failure": None, "error": error,
                "report": f"{self.suite.upper()} TESTS: infrastructure error ({error})"}

    def selftest(self):
        code, data = self._json("selftest", timeout=300)
        if data is None or "checks" not in data:
            raise JudgeError(f"judge selftest failed: {(data or {}).get('error', 'no output')}")
        return data


def _add_bytes(archive, name, data):
    """Deterministic member (fixed mtime, owner and mode) so the fingerprint is stable."""
    info = tarfile.TarInfo(name)
    info.size, info.mtime, info.mode = len(data), 0, 0o644
    archive.addfile(info, io.BytesIO(data))
