"""Export descriptive pilot metrics without reading private test contents."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", type=Path)
    args = parser.parse_args()
    batch = args.batch.resolve(strict=True)
    if batch.drive.upper() != "E:":
        parser.error("Metrics must remain with the E: batch artifacts")
    rows = []
    fields = ["run_id", "model", "task_id", "status", "elapsed_seconds", "actions", "repairs",
              "format_errors", "public_test_failures", "command_failures"]
    for path in sorted(batch.glob("*/result.json")):
        result = json.loads(path.read_text())
        evaluation_path = path.parent / "private_evaluation.json"
        evaluation = json.loads(evaluation_path.read_text()) if evaluation_path.exists() else {"status": "not_evaluated"}
        rows.append({key: result.get(key) for key in fields} | {"official_status": evaluation["status"]})
    if not rows:
        parser.error("No run records found")
    models = {}
    for model in dict.fromkeys(row["model"] for row in rows):
        selected = [row for row in rows if row["model"] == model]
        models[model] = {"completed": len(selected),
                         "passed": sum(row["official_status"] == "pass" for row in selected),
                         "missing_submissions": sum(row["official_status"] == "missing_submission" for row in selected),
                         "infrastructure_errors": sum(row["official_status"] == "infrastructure_error" for row in selected),
                         **{key: round(sum(row.get(key) or 0 for row in selected), 3)
                            for key in ("elapsed_seconds", "actions", "repairs", "format_errors", "public_test_failures")}}
    expected = json.loads((batch / "implementation.json").read_text())["sha256"]
    root = Path(__file__).resolve().parent
    unchanged = all(hashlib.sha256((root / name).read_bytes()).hexdigest() == digest for name, digest in expected.items())
    with (batch / "metrics.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (batch / "summary.json").write_text(json.dumps({"current_source_matches_run": unchanged, "models": models, "rows": rows}, indent=2), encoding="utf-8")
    print(json.dumps({"batch": str(batch), "current_source_matches_run": unchanged, "models": models}, indent=2))


if __name__ == "__main__":
    main()
