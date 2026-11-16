"""Optional fixed 3x3 local-only pilot. Requires a successful isolated smoke test."""
import argparse
import hashlib
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path

from prepare_lcb import EVALUATOR_REVISION
from runner import ROOT, docker, isolation_preflight, write_json


def score(run, row_path, vendor, image):
    source = run / "solution.py"
    if not source.is_file():
        return {"status": "missing_submission"}
    name = "csc2108-lcb-" + uuid.uuid4().hex[:12]
    payload = {"source": source.read_text(encoding="utf-8"), "row": json.loads(row_path.read_text())}
    try:
        result = docker("run", "--name", name, "--rm", "--pull", "never", "-i", "--network", "none",
                        "--read-only", "--memory", "1g", "--memory-swap", "1g", "--cpus", "1",
                        "--pids-limit", "64", "--user", "65534:65534", "--cap-drop", "ALL",
                        "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,nosuid,size=128m,mode=1777",
                        "--mount", f"type=bind,src={vendor},dst=/opt/lcb,readonly",
                        "--mount", f"type=bind,src={ROOT / 'judge_lcb.py'},dst=/judge.py,readonly",
                        image, "python", "-I", "/judge.py", input=json.dumps(payload), timeout=180)
        (run / "judge.stdout.txt").write_text(result.stdout, encoding="utf-8")
        (run / "judge.stderr.txt").write_text(result.stderr, encoding="utf-8")
        lines = [line for line in result.stdout.splitlines() if line.startswith("CSC2108_EVALUATION=")]
        return json.loads(lines[-1].split("=", 1)[1])
    except Exception as exc:
        return {"status": "infrastructure_error", "error_type": type(exc).__name__, "error": str(exc)}
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=15)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset-root", type=Path, default=Path("E:/CSC2108Local/lcb-v1"))
    p.add_argument("--vendor", type=Path, default=Path("E:/CSC2108Local/vendor/LiveCodeBench"))
    p.add_argument("--docker-disk-root", type=Path, default=Path("E:/DockerDesktop"))
    p.add_argument("--judge-image", default="csc2108-lcb-judge:v1")
    p.add_argument("--smoke-result", type=Path, required=True,
                   help="A real passing isolated smoke result.json; infrastructure probes do not qualify")
    args = p.parse_args()
    smoke = json.loads(args.smoke_result.read_text())
    public_outcomes = [e["returncode"] for e in smoke.get("events", []) if e.get("recognized_public_test")]
    if (smoke.get("task_id") != "fixture-sum-signed" or smoke.get("status") != "Submitted"
            or smoke.get("independent_evaluation", {}).get("status") != "pass"
            or len(public_outcomes) < 2 or not public_outcomes[0] or public_outcomes[-1]):
        p.error("Complete the isolated smoke task before starting the pilot")
    manifest = json.loads((args.dataset_root / "manifest.json").read_text())
    frozen = json.loads((ROOT / "lcb_manifest.json").read_text())
    if manifest != frozen:
        p.error("Dataset manifest differs from the frozen manifest")
    vendor = args.vendor.resolve(strict=True)
    revision = subprocess.run(["git", "-C", str(vendor), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(vendor), "status", "--porcelain"], check=True, capture_output=True, text=True).stdout
    if revision != EVALUATOR_REVISION or dirty:
        p.error("Official evaluator checkout must be clean at the pinned revision")
    isolation = isolation_preflight(args.judge_image, args.docker_disk_root)
    batch = Path("E:/CSC2108Local/artifacts/pilots") / (time.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8])
    batch.mkdir(parents=True)
    records = []
    write_json(batch / "manifest.json", manifest)
    write_json(batch / "judge_configuration.json", isolation)
    source_files = ["runner.py", "probe.py", "pilot.py", "judge_lcb.py", "models.json", "requirements.lock", "judge-requirements.lock"]
    source_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_files}
    write_json(batch / "implementation.json", {"sha256": source_hashes, "actions": 20, "repairs": 3, "seconds": 600})
    for model in json.loads((ROOT / "models.json").read_text()):
        for task in manifest["tasks"]:
            if source_hashes != {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_files}:
                raise RuntimeError("Implementation changed during the frozen pilot")
            public = args.dataset_root / "public" / task["task_id"]
            actual = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in public.iterdir()}
            if actual != task["public_sha256"]:
                raise ValueError("Public task changed after freezing")
            invocation = subprocess.run([sys.executable, str(ROOT / "runner.py"), "--model", model,
                                        "--protocol", "text", "--task", str(public), "--output", str(batch),
                                        "--docker-disk-root", str(args.docker_disk_root)],
                                       capture_output=True, text=True, timeout=720)
            item = {"model": model, "task_id": task["task_id"], "stdout": invocation.stdout, "stderr": invocation.stderr}
            try:
                summary = json.loads(invocation.stdout.splitlines()[-1])
                run = Path(summary["run"])
                item.update(run=str(run), agent_status=summary["status"],
                            evaluation=score(run, args.dataset_root / "evaluator_private" / (task["task_id"] + ".json"), vendor, args.judge_image))
                write_json(run / "private_evaluation.json", item["evaluation"])
            except Exception as exc:
                item.update(status="infrastructure_error", error=str(exc))
            records.append(item)
            write_json(batch / "results.json", records)
            print(json.dumps({"model": model, "task_id": task["task_id"], "run": item.get("run"),
                              "agent_status": item.get("agent_status"),
                              "evaluation": item.get("evaluation", {}).get("status", item.get("status"))}), flush=True)


if __name__ == "__main__":
    main()
