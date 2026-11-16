"""Condition A only: mini-SWE-agent v2, local Ollama, disposable Docker tasks."""
import argparse
import base64
import hashlib
import json
import os
import shlex
import subprocess
import time
import uuid
from pathlib import Path

os.environ.setdefault("MSWEA_MODEL_RETRY_STOP_AFTER_ATTEMPT", "1")
os.environ.setdefault("MSWEA_SILENT_STARTUP", "1")
from minisweagent.agents.default import DefaultAgent
from minisweagent.environments.docker import DockerEnvironment
from minisweagent.exceptions import InterruptAgentFlow
import requests

from probe import ENDPOINT, ROOT, PROTOCOL_VERSION, make_model, system_prompt, unload_project_models

PUBLIC_COMMAND = "python -I /public/check.py"
IMAGE = "python:3.11-slim-bookworm"
MAX_SOURCE = 1024 * 1024


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def docker(*args, timeout=30, input=None):
    return subprocess.run(["docker", *args], input=input, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=timeout, check=True)


def isolation_preflight(image, disk_root):
    # Windows DockerRootDir is a guest path; demand host-side disk evidence too.
    disk_root = disk_root.resolve(strict=True)
    if disk_root.drive.upper() != "E:":
        raise ValueError("Docker disk evidence must be on E:")
    disks = [{"path": str(p), "bytes": p.stat().st_size} for p in disk_root.rglob("*.vhdx")]
    if os.name == "nt" and not disks:
        raise ValueError("No Docker VHDX found at the declared E: disk location")
    info = json.loads(docker("info", "--format", "{{json .}}", timeout=15).stdout)
    if info.get("OSType") != "linux" or not info.get("MemoryLimit") or not info.get("PidsLimit"):
        raise RuntimeError("A Linux Docker daemon with memory and PID limits is required")
    if os.name == "nt":
        settings = json.loads((Path(os.environ["APPDATA"]) / "Docker/settings-store.json").read_text())
        configured = settings.get("CustomWslDistroDir") or settings.get("customWslDistroDir")
        if not configured or Path(configured).resolve() != disk_root:
            raise RuntimeError("Docker Desktop WSL disk setting does not match the declared E: disk location")
    image_info = json.loads(docker("image", "inspect", image).stdout)[0]
    return {"docker": {k: info.get(k) for k in ("ServerVersion", "DockerRootDir", "OSType")},
            "disk_root": str(disk_root), "disks": disks,
            "image_id": image_info["Id"], "image_digests": image_info.get("RepoDigests")}


def limits(reason):
    return InterruptAgentFlow({"role": "exit", "content": reason,
                               "extra": {"exit_status": reason, "submission": ""}})


class Budget:
    """Edits after a recognized failed public test form a repair until a changed retest."""
    def __init__(self, actions=20, repairs=3):
        self.action_limit, self.repair_limit = actions, repairs
        self.actions = self.repairs = 0
        self.failed_hash = None
        self.repairing = False
        self.events = []

    def before(self):
        if self.actions >= self.action_limit:
            raise limits("ActionLimit")
        self.actions += 1

    def changed(self, before, after):
        if self.failed_hash is not None and not self.repairing and after != before:
            self.repairs += 1
            self.repairing = True
            self.events.append({"event": "repair_start", "repair": self.repairs, "action": self.actions})
            if self.repairs > self.repair_limit:
                # Changes are recorded, but this run's submission is the previous candidate.
                raise limits("RepairLimit")

    def tested(self, digest, returncode):
        if digest != self.failed_hash:
            self.repairing = False
        self.failed_hash = digest if returncode else None


class TaskEnvironment(DockerEnvironment):
    """Only public files mounted. No repository, Docker socket, or evaluator access."""
    def __init__(self, *, budget, deadline, evidence, **kwargs):
        self.budget, self.deadline, self.evidence = budget, deadline, evidence
        self.last_candidate = None
        super().__init__(**kwargs)

    def cleanup(self):
        # Upstream cleanup is POSIX shell syntax; this implementation also works on Windows.
        container_id = getattr(self, "container_id", None)
        if container_id:
            try:
                docker("rm", "-f", container_id, timeout=15)
            except (OSError, subprocess.SubprocessError):
                pass
            self.container_id = None

    def snapshot(self):
        # Read as bytes inside container; never follow candidate symlinks or execute it on host.
        script = (
            "import os,stat,base64; p='/workspace/solution.py'; "
            "f=os.open(p,os.O_RDONLY|os.O_NOFOLLOW); s=os.fstat(f); "
            f"assert stat.S_ISREG(s.st_mode) and s.st_size<={MAX_SOURCE}; "
            f"print(base64.b64encode(os.read(f,{MAX_SOURCE + 1})).decode())"
        )
        try:
            return base64.b64decode(docker("exec", self.container_id, "python", "-I", "-c", script, timeout=5).stdout, validate=False)
        except subprocess.CalledProcessError:
            return None

    def execute(self, action, cwd="", *, timeout=None):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise limits("Deadline")
        self.budget.before()
        before = self.snapshot()
        started = time.monotonic()
        command = action.get("command", "")
        if not isinstance(command, str):
            raise ValueError("Command must be a string")
        # A timeout kills the whole task container, including surviving child processes.
        log_path = "/tmp/action-" + uuid.uuid4().hex + ".log"
        wrapped = (f"ulimit -f 2048; timeout -k 1 {max(0.1, min(27, remaining - 1)):.2f}s "
                   f"bash -lc {shlex.quote(command)} >{log_path} 2>&1; "
                   f"rc=$?; head -c 16384 {log_path}; rm -f {log_path}; exit $rc")
        try:
            output = super().execute(action | {"command": wrapped}, cwd, timeout=max(0.1, min(30, remaining)))
        except InterruptAgentFlow:
            after = self.snapshot()
            self.last_candidate = after
            try:
                self.budget.changed(before, after)
            except InterruptAgentFlow:
                self.last_candidate = before
                raise
            self.evidence.append({"command": command, "submitted": True, "action": self.budget.actions})
            raise
        after = self.snapshot()
        self.last_candidate = after
        digest = hashlib.sha256(after).hexdigest() if after is not None else None
        event = {"command": command, "action": self.budget.actions,
                 "elapsed_seconds": time.monotonic() - started, "source_sha256": digest, **output}
        self.evidence.append(event)
        if output.get("exception_info") or output["returncode"] in (124, 137, 153):
            self.cleanup()
            raise limits("CommandExecutionError")
        if output["returncode"] in (125, 126, 127) and "Error response from daemon" in output["output"]:
            raise limits("InfrastructureError")
        try:
            self.budget.changed(before, after)
        except InterruptAgentFlow:
            self.last_candidate = before
            raise
        if command.strip() == PUBLIC_COMMAND:
            self.budget.tested(digest, output["returncode"])
            event["recognized_public_test"] = True
        return output


class TimedAgent(DefaultAgent):
    def query(self):
        remaining = self.env.deadline - time.monotonic()
        if remaining <= 0:
            raise limits("Deadline")
        self.model.config.model_kwargs["timeout"] = max(0.1, min(120, remaining))
        return super().query()


def container_args(public):
    return ["--rm", "--pull", "never", "--network", "none", "--read-only",
            "--memory", "512m", "--memory-swap", "512m", "--cpus", "1", "--pids-limit", "64",
            "--user", "65534:65534", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m,mode=1777",
            "--tmpfs", "/workspace:rw,nosuid,size=64m,mode=1777",
            "--mount", f"type=bind,src={public},dst=/public,readonly"]


def independent_evaluate(source, public, image):
    """Fresh container, pristine visible tests. Fixture-only additional checks stay here."""
    name = "csc2108-judge-" + uuid.uuid4().hex[:12]
    # No benchmark reference solution is included here; arithmetic oracle is fixture-only.
    extra = ""
    if json.loads((public / "task.json").read_text())["task_id"] == "fixture-sum-signed":
        extra = ("; import importlib.util; s=importlib.util.spec_from_file_location('s','/workspace/solution.py'); "
                 "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
                 "assert all(m.signed_sum(a,b)==a+b for a,b in [(0,-8),(-9,-11),(10**50,-1)])")
    script = ("import base64,sys,pathlib,subprocess; "
              "pathlib.Path('/workspace/solution.py').write_bytes(base64.b64decode(sys.stdin.read())); "
              "r=subprocess.run(['python','-I','/public/check.py'],timeout=15); "
              "assert r.returncode==0" + extra)
    try:
        result = docker("run", "--name", name, "-i", *container_args(public), image,
                        "python", "-I", "-c", script,
                        input=base64.b64encode(source).decode(), timeout=25)
        return {"status": "pass", "stdout": result.stdout, "stderr": result.stderr,
                "scope": "fixture public plus independent cases" if extra else "public tests only"}
    except subprocess.CalledProcessError as exc:
        return {"status": "infrastructure_error" if exc.returncode in (125, 126, 127) else "candidate_failure",
                "returncode": exc.returncode, "stdout": exc.stdout, "stderr": exc.stderr}
    except subprocess.TimeoutExpired:
        return {"status": "candidate_timeout"}
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=15)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", required=True)
    p.add_argument("--protocol", choices=["native", "text"], default="text")
    p.add_argument("--task", type=Path, default=ROOT / "fixtures/signed_sum")
    p.add_argument("--output", type=Path, default=Path("E:/CSC2108Local/artifacts/runs"))
    p.add_argument("--docker-disk-root", type=Path, default=Path("E:/DockerDesktop"))
    p.add_argument("--image", default=IMAGE)
    p.add_argument("--actions", type=int, default=20)
    p.add_argument("--repairs", type=int, default=3)
    p.add_argument("--seconds", type=int, default=600)
    args = p.parse_args()
    if not 1 <= args.actions <= 100 or not 0 <= args.repairs <= 20 or not 1 <= args.seconds <= 900:
        p.error("Invalid limits")
    if args.output.resolve().drive.upper() != "E:":
        p.error("Artifacts must be on E:")
    run = args.output / (time.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8])
    run.mkdir(parents=True, exist_ok=False)
    record = {"run_id": run.name, "condition": "A", "model": args.model,
              "protocol": args.protocol, "protocol_version": PROTOCOL_VERSION,
              "configuration": vars(args) | {"task": str(args.task), "output": str(args.output), "docker_disk_root": str(args.docker_disk_root)},
              "status": "infrastructure_error", "events": []}
    env = agent = None
    started = time.monotonic()
    budget = Budget(args.actions, args.repairs)
    try:
        public = args.task.resolve(strict=True)
        # This directory is the entire read-only agent-visible mount. Keep private data elsewhere.
        permitted = {"task.json", "check.py", "solution.py", "public_tests.json"}
        if any(p.name not in permitted or p.is_symlink() or p.is_dir() for p in public.iterdir()):
            raise ValueError("Task directory contains unexpected files; refusing to expose it")
        task = json.loads((public / "task.json").read_text(encoding="utf-8"))
        if set(task) != {"task_id", "version", "statement", "submission_path"} or task["submission_path"] != "solution.py":
            raise ValueError("Invalid public task schema")
        record.update(task_id=task["task_id"], task_version=task["version"],
                      task_files={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in public.iterdir()})
        record["isolation"] = isolation_preflight(args.image, args.docker_disk_root)
        unload_project_models()
        model = make_model(args.model, args.protocol)
        record["model_tags"] = requests.get(ENDPOINT + "/api/tags", timeout=10).json()
        env = TaskEnvironment(budget=budget, deadline=started + args.seconds, evidence=record["events"],
                              image=args.image, cwd="/workspace", run_args=container_args(public),
                              container_timeout=str(args.seconds + 60) + "s",
                              env={"PYTHONDONTWRITEBYTECODE": "1", "HOME": "/tmp"})
        # Trusted initialization is not an agent tool action.
        if (public / "solution.py").exists():
            docker("exec", env.container_id, "cp", "/public/solution.py", "/workspace/solution.py")
        template = system_prompt(args.protocol) + " Your working directory is /workspace."
        template += (" Run the exact visible test command python -I /public/check.py as a separate action to receive recognized test feedback. "
                     "You may read files and edit /workspace/solution.py. Commands use fresh shells. "
                     "Finish with the separate command echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT.")
        agent = TimedAgent(model, env, system_template=template, instance_template="{{task}}",
                           step_limit=args.actions + 5, cost_limit=0, wall_time_limit_seconds=args.seconds,
                           output_path=run / "trajectory.json")
        write_json(run / "task.json", task)
        write_json(run / "configuration.json", agent.serialize())
        exit_info = agent.run(task["statement"])
        record.update(status=exit_info.get("exit_status", "unknown"), exit_info=exit_info)
    except Exception as exc:
        record.update(error_type=type(exc).__name__, error=str(exc))
    finally:
        record.update(elapsed_seconds=time.monotonic() - started, actions=budget.actions,
                      repairs=min(budget.repairs, budget.repair_limit), repair_events=budget.events)
        source = env.last_candidate if env else None
        if env and env.container_id and source is None:
            try:
                source = env.snapshot()
            except Exception as exc:
                record["extraction_error"] = str(exc)
        if source is not None:
            (run / "solution.py").write_bytes(source)
            record["submission_sha256"] = hashlib.sha256(source).hexdigest()
        if agent:
            agent.save(run / "trajectory.json")
        if env:
            env.cleanup()
        if source is not None:
            try:
                record["independent_evaluation"] = independent_evaluate(source, public, args.image)
            except Exception as exc:
                record["independent_evaluation"] = {"status": "infrastructure_error", "error": str(exc)}
        try:
            record["ollama_ps"] = requests.get(ENDPOINT + "/api/ps", timeout=10).json()
            record["gpu"] = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader"], capture_output=True, text=True).stdout
        except Exception as exc:
            record["telemetry_error"] = str(exc)
        record["format_errors"] = sum(m.get("extra", {}).get("interrupt_type") == "FormatError"
                                      for m in (agent.messages if agent else []))
        record["command_failures"] = sum(bool(e.get("returncode")) for e in record["events"])
        record["public_test_failures"] = sum(e.get("recognized_public_test", False) and bool(e.get("returncode"))
                                             for e in record["events"])
        status = record["status"]
        if status == "infrastructure_error":
            category = "model_timeout" if "Timeout" in record.get("error_type", "") else "infrastructure_error"
        elif status == "RepeatedFormatError":
            category = "malformed_actions"
        elif status in ("TimeExceeded", "Deadline"):
            category = "task_timeout"
        elif status == "CommandExecutionError":
            category = "command_timeout_or_resource_error"
        elif status in ("LimitsExceeded", "ActionLimit", "RepairLimit"):
            category = "budget_exhausted"
        elif status == "Submitted":
            category = "submitted"
        else:
            category = "execution_error"
        record["termination_category"] = category
        write_json(run / "result.json", record)
    print(json.dumps({"run": str(run), "status": record["status"], "evaluation": record.get("independent_evaluation")}))


if __name__ == "__main__":
    main()
