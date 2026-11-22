"""Rebuild tasks/ (and optionally hidden/) from the frozen manifests.

    python3 build_data.py            # tasks/: statements, task.json, public tests
    python3 build_data.py --hidden   # also hidden/: hidden tests (for judge-hidden)

Downloads the pinned LiveCodeBench shard into .cache/, checks its sha256,
converts exactly the tasks listed in manifests/*.json, and checks every
task's test hashes against the manifest. Any mismatch is an error, so two
machines either end up with identical data or the build fails.
Standard library only.
"""
import argparse
import base64
import hashlib
import io
import json
import pickle
import shutil
import sys
import urllib.request
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFESTS = ROOT / "manifests"
TASKS_DIR, HIDDEN_DIR, CACHE_DIR = ROOT / "tasks", ROOT / "hidden", ROOT / ".cache"

DATASET = "livecodebench/code_generation_lite"
SHARDS = {  # shard -> sha256 of the file at the pinned revision
    "test6.jsonl": "bb4c364f71921c4495a6ad15abe1a927350b720009f4933e2e71f8af0f6fd1f5",
}
TIME_LIMIT_S = 6.0
SUBMISSION_NOTE = """
## Submission

Write a Python 3 program that reads the input from standard input and prints
the answer to standard output.
"""


class _StringOnlyUnpickler(pickle.Unpickler):
    """LCB private tests are a pickled JSON *string*; refuse anything else."""

    def find_class(self, module, name):
        raise pickle.UnpicklingError(f"refusing to load {module}.{name}")


def decode_private(blob):
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        raw = zlib.decompress(base64.b64decode(blob.encode("ascii")))
        value = _StringOnlyUnpickler(io.BytesIO(raw)).load()
        if not isinstance(value, (str, bytes)):
            raise ValueError("unexpected private test payload type")
        return json.loads(value)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_dir(path):
    """Hash over file names and contents (same definition as the manifests)."""
    digest = hashlib.sha256()
    for file in sorted(Path(path).iterdir()):
        digest.update(file.name.encode() + b"\0" + file.read_bytes() + b"\0")
    return digest.hexdigest()


def load_manifests():
    tasks, revisions, shards = {}, set(), set()
    for path in sorted(MANIFESTS.glob("*.json")):
        manifest = json.loads(path.read_text())
        revisions.update(manifest["hf_revision"])
        shards.update(manifest["shards"])
        for entry in manifest["tasks"]:
            tasks[entry["task_id"]] = entry
    if len(revisions) != 1:
        sys.exit(f"manifests must pin exactly one dataset revision, found {sorted(revisions)}")
    unknown = shards - SHARDS.keys()
    if unknown:
        sys.exit(f"no pinned sha256 for shards {sorted(unknown)}; add them to SHARDS")
    return tasks, revisions.pop(), sorted(shards)


def fetch(shard, revision):
    CACHE_DIR.mkdir(exist_ok=True)
    target = CACHE_DIR / f"{revision[:12]}-{shard}"
    if target.exists() and sha256_file(target) == SHARDS[shard]:
        return target
    url = f"https://huggingface.co/datasets/{DATASET}/resolve/{revision}/{shard}"
    print(f"downloading {url}", flush=True)
    partial = target.with_suffix(".part")
    with urllib.request.urlopen(url, timeout=60) as response, open(partial, "wb") as out:
        shutil.copyfileobj(response, out, 1 << 20)
    actual = sha256_file(partial)
    if actual != SHARDS[shard]:
        partial.unlink()
        sys.exit(f"{shard}: sha256 {actual} does not match the pinned {SHARDS[shard]}")
    partial.rename(target)
    return target


def write_cases(directory, cases):
    directory.mkdir(parents=True)
    for index, case in enumerate(cases, 1):
        # newline="": write LF bytes on every OS, so Windows builds match the manifest hashes
        (directory / f"{index:02d}.in").write_text(case["input"], encoding="utf-8", newline="")
        (directory / f"{index:02d}.out").write_text(case["output"], encoding="utf-8", newline="")


def build(row, entry, shard, revision, with_hidden):
    task_id = entry["task_id"]
    task_dir = TASKS_DIR / task_id
    public = json.loads(row["public_test_cases"])
    write_cases(task_dir / "tests" / "public", public)
    (task_dir / "problem.md").write_text(
        f"# {row['question_title']}\n\n{row['question_content'].strip()}\n{SUBMISSION_NOTE}",
        encoding="utf-8")
    meta = {"task_id": task_id, "version": entry["version"], "submission_type": "stdin_stdout",
            "difficulty": row["difficulty"], "time_limit_s": TIME_LIMIT_S,
            "n_public": len(public), "n_hidden": entry["n_hidden"],
            "public_sha256": sha256_dir(task_dir / "tests" / "public"),
            "hidden_sha256": entry["hidden_sha256"],
            "source": {"dataset": DATASET, "hf_revision": revision, "shard": shard,
                       "platform": row["platform"], "question_id": row["question_id"],
                       "contest_id": row["contest_id"], "contest_date": row["contest_date"],
                       "title": row["question_title"]}}
    (task_dir / "task.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    errors = []
    if meta["public_sha256"] != entry["public_sha256"]:
        errors.append("public tests")
    if with_hidden:
        write_cases(HIDDEN_DIR / task_id, decode_private(row["private_test_cases"]))
        if sha256_dir(HIDDEN_DIR / task_id) != entry["hidden_sha256"]:
            errors.append("hidden tests")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--hidden", action="store_true", help="also build hidden/")
    args = parser.parse_args()
    wanted, revision, shards = load_manifests()

    for directory in (TASKS_DIR, HIDDEN_DIR) if args.hidden else (TASKS_DIR,):
        shutil.rmtree(directory, ignore_errors=True)
        directory.mkdir()
    done, failures = set(), {}
    for shard in shards:
        with fetch(shard, revision).open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                task_id = f"lcb-{row['platform']}-{row['question_id']}"
                if task_id in wanted and task_id not in done:
                    errors = build(row, wanted[task_id], shard, revision, args.hidden)
                    if errors:
                        failures[task_id] = errors
                    done.add(task_id)
    missing = sorted(set(wanted) - done)
    if missing or failures:
        sys.exit(f"build failed: missing {missing}, hash mismatch {failures}")
    built = "tasks/ and hidden/" if args.hidden else "tasks/"
    print(f"built {built} for {len(done)} tasks; all hashes match manifests/")


if __name__ == "__main__":
    main()
