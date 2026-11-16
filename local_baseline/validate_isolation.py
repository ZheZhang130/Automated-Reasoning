"""Trusted fixture checks of containment and feedback before model-driven runs."""
import argparse
import json
import time
import uuid
from pathlib import Path

from minisweagent.exceptions import InterruptAgentFlow
from runner import (Budget, IMAGE, PUBLIC_COMMAND, ROOT, TaskEnvironment,
                    container_args, docker, independent_evaluate, isolation_preflight, write_json)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--docker-disk-root", type=Path, default=Path("E:/DockerDesktop"))
    args = p.parse_args()
    output = Path("E:/CSC2108Local/artifacts/isolation") / uuid.uuid4().hex
    output.mkdir(parents=True)
    public = ROOT / "fixtures/signed_sum"
    record = {"status": "error", "events": [], "model_calls": 0}
    env = None
    try:
        record["preflight"] = isolation_preflight(IMAGE, args.docker_disk_root)
        env = TaskEnvironment(budget=Budget(), deadline=time.monotonic() + 90,
                              evidence=record["events"], image=IMAGE, cwd="/workspace",
                              run_args=container_args(public), container_timeout="100s")
        inspect = json.loads(docker("inspect", env.container_id).stdout)[0]
        hc = inspect["HostConfig"]
        record["container"] = {"host_config": hc, "mounts": inspect["Mounts"], "user": inspect["Config"]["User"]}
        assert hc["ReadonlyRootfs"] and hc["NetworkMode"] == "none"
        assert hc["Memory"] == hc["MemorySwap"] == 512 * 1024 * 1024
        assert hc["NanoCpus"] == 10**9 and hc["PidsLimit"] == 64
        assert inspect["Config"]["User"] == "65534:65534"
        binds = [m for m in inspect["Mounts"] if m["Type"] == "bind"]
        assert len(binds) == 1 and binds[0]["Destination"] == "/public" and not binds[0]["RW"]
        docker("exec", env.container_id, "cp", "/public/solution.py", "/workspace/solution.py")
        assert env.execute({"command": "id -u"})["output"].strip() == "65534"
        assert env.execute({"command": "touch /isolation_write_probe"})["returncode"] != 0
        assert env.execute({"command": "test ! -S /var/run/docker.sock"})["returncode"] == 0
        failed = env.execute({"command": PUBLIC_COMMAND})
        assert failed["returncode"] == 1 and "FAILED" in failed["output"]
        source = env.snapshot()
        record["independent_wrong_candidate"] = independent_evaluate(source, public, IMAGE)
        assert record["independent_wrong_candidate"]["status"] == "candidate_failure"
        try:
            env.execute({"command": "sleep 60"})
            raise AssertionError("Long-running command was not stopped")
        except InterruptAgentFlow as exc:
            assert exc.messages[-1]["extra"]["exit_status"] == "CommandExecutionError"
            assert env.container_id is None
        record["status"] = "pass"
    except Exception as exc:
        record.update(error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        if env:
            env.cleanup()
        write_json(output / "result.json", record)
        print(json.dumps({"output": str(output), "status": record["status"]}))


if __name__ == "__main__":
    main()
