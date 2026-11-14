"""Host-side client for the csc2108 judge container (standard library only).

    from judgekit import Judge
    judge = Judge.public()                       # starts judge-public if needed
    result = judge.run("lcb-atcoder-abc393_a", code)

See timeline/judge_1114.md for the result schema. Requires a running Docker engine
(Docker Desktop, OrbStack or Colima).
"""
import io
import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path

__all__ = ["Judge", "JudgeError", "IMAGE", "JUDGE_VERSION"]

JUDGE_VERSION = "0.2.0"
IMAGE = os.environ.get("JUDGE_IMAGE", f"csc2108-judge:{JUDGE_VERSION}")
EVAL_ROOT = Path(__file__).resolve().parent.parent
SUITES = ("public", "hidden")
NPROC_PER_SLOT = 64


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
        return subprocess.run([self.docker, *args], input=stdin, capture_output=True,
                              timeout=timeout)

    def _state(self):
        proc = self._call("inspect", "-f", "{{.State.Running}} {{.Config.Image}}", self.name)
        if proc.returncode != 0:
            return None
        running, image = proc.stdout.decode().split()
        return running == "true", image

    def up(self, force=False):
        """Start (or reuse) the container and load the suite. Returns `info()`."""
        state = self._state()
        if state and not force and state == (True, self.image):
            try:
                info = self.info()
                if info["suite"] == self.suite and (self.tasks is None
                                                    or info["tasks"] == self.tasks):
                    return info
            except JudgeError:
                pass
        self.down()
        proc = self._call("run", "-d", "--name", self.name,
                          "--label", f"csc2108.judge.suite={self.suite}",
                          *container_flags(self.cpus), self.image, "sleep", "infinity")
        if proc.returncode != 0:
            raise JudgeError(f"docker run failed: {proc.stderr.decode().strip()}")
        self.load()
        return self.info()

    def down(self):
        self._call("rm", "-f", self.name)

    def load(self):
        """Stream the suite's tests into the container (no bind mount)."""
        archive = self._suite_archive()
        proc = self._call("exec", "-i", "-u", "0", self.name, "judge", "load",
                          "--suite", self.suite, stdin=archive, timeout=600)
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
                        archive.add(path, arcname=f"{task_id}/{path.name}", recursive=False)
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
            if status == 0 and data and "status" in data:
                return data
            last = data
        if last and last.get("status") == "infrastructure_error":
            return last
        error = (last or {}).get("error", "judge produced no result")
        return {"judge_version": None, "suite": self.suite, "task_id": task_id,
                "status": "infrastructure_error", "passed": 0, "total": 0,
                "verdict_counts": {}, "cases": [], "first_failure": None, "error": error,
                "report": f"{self.suite.upper()} TESTS: infrastructure error ({error})"}

    def selftest(self):
        code, data = self._json("selftest", timeout=300)
        if data is None or "checks" not in data:
            raise JudgeError(f"judge selftest failed: {(data or {}).get('error', 'no output')}")
        return data


def _add_bytes(archive, name, data):
    info = tarfile.TarInfo(name)
    info.size = len(data)
    archive.addfile(info, io.BytesIO(data))
