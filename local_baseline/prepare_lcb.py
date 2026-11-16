"""Freeze three public task bundles. Hidden rows remain outside agent mounts."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from urllib.request import urlopen

DATASET_REVISION = "0fe84c3912ea0c4d4a78037083943e8f0c4dd505"
EVALUATOR_REVISION = "28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24"
URL = f"https://huggingface.co/datasets/livecodebench/code_generation_lite/resolve/{DATASET_REVISION}/test.jsonl"
ROOT = Path(__file__).resolve().parent


def export(rows, output):
    output.mkdir(parents=True, exist_ok=False)
    public_root, private_root = output / "public", output / "evaluator_private"
    private_root.mkdir()
    selected = []
    for difficulty in ("easy", "medium", "hard"):
        eligible = [r for r in rows if r["difficulty"] == difficulty
                    and not json.loads(r["metadata"]).get("func_name")
                    and json.loads(r["public_test_cases"])
                    and all(t["testtype"] == "stdin" for t in json.loads(r["public_test_cases"]))]
        row = sorted(eligible, key=lambda r: (r["platform"], r["question_id"]))[0]
        task_id = row["platform"] + "-" + row["question_id"]
        task_root = public_root / task_id
        task_root.mkdir(parents=True)
        task = {"task_id": task_id, "version": DATASET_REVISION,
                "statement": row["question_content"] + "\n\nWrite a standalone stdin/stdout Python program in /workspace/solution.py. "
                "Visible development tests: python -I /public/check.py. Final submission: echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT.",
                "submission_path": "solution.py"}
        (task_root / "task.json").write_text(json.dumps(task, indent=2), encoding="utf-8")
        (task_root / "public_tests.json").write_text(row["public_test_cases"], encoding="utf-8")
        shutil.copyfile(ROOT / "public_stdio_check.py", task_root / "check.py")
        # Save raw private fields without decoding the dataset's pickle format on the host.
        (private_root / (task_id + ".json")).write_text(json.dumps(row), encoding="utf-8")
        selected.append({"task_id": task_id, "question_id": row["question_id"],
                         "platform": row["platform"], "difficulty": difficulty,
                         "public_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in task_root.iterdir()}})
    manifest = {"dataset": "livecodebench/code_generation_lite", "revision": DATASET_REVISION,
                "release": "release_v1", "file": "test.jsonl", "evaluator_revision": EVALUATOR_REVISION,
                "selection_rule": "First lexicographic (platform,question_id) stdin task with visible tests per difficulty; fixed before runs",
                "tasks": selected}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=Path("E:/CSC2108Local/lcb-v1"))
    p.add_argument("--cache", type=Path, default=Path("E:/CSC2108Local/cache/lcb/test.jsonl"))
    args = p.parse_args()
    if any(p.resolve().drive.upper() != "E:" for p in (args.output, args.cache)):
        p.error("Dataset and output paths must be on E:")
    args.cache.parent.mkdir(parents=True, exist_ok=True)
    if not args.cache.exists():
        partial = args.cache.with_suffix(".partial")
        with urlopen(URL, timeout=120) as response, partial.open("wb") as target:
            shutil.copyfileobj(response, target)
        partial.rename(args.cache)
    rows = [json.loads(line) for line in args.cache.read_text(encoding="utf-8").splitlines()]
    manifest = export(rows, args.output)
    manifest["source_sha256"] = hashlib.sha256(args.cache.read_bytes()).hexdigest()
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
