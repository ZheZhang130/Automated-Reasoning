"""Validate official scoring on synthetic fixtures, never benchmark solutions."""
import base64
import json
import pickle
import uuid
import zlib
from pathlib import Path

from pilot import score
from runner import isolation_preflight, write_json


def main():
    root = Path("E:/CSC2108Local/artifacts/judge-validation") / uuid.uuid4().hex
    root.mkdir(parents=True)
    record = {"isolation": isolation_preflight("csc2108-lcb-judge:v1", Path("E:/DockerDesktop")), "cases": []}
    cases = [{"input": "", "output": "JUDGE_OK\n", "testtype": "stdin"}]
    row = {"public_test_cases": json.dumps(cases), "private_test_cases": json.dumps(cases), "metadata": "{}"}
    for label, source, expected in [
        ("correct", "print('JUDGE_OK')\n", "pass"),
        ("wrong", "print('WRONG')\n", "candidate_failure"),
        ("syntax", "def broken(\n", "candidate_failure"),
        ("timeout", "while True: pass\n", "candidate_failure"),
        ("pickle_correct", "print('JUDGE_OK')\n", "pass"),
    ]:
        run = root / label
        run.mkdir()
        (run / "solution.py").write_text(source, encoding="utf-8")
        current = dict(row)
        if label == "pickle_correct":
            current["private_test_cases"] = base64.b64encode(zlib.compress(pickle.dumps(json.dumps(cases)))).decode()
        row_path = run / "row.json"
        write_json(row_path, current)
        evaluation = score(run, row_path, Path("E:/CSC2108Local/vendor/LiveCodeBench"), "csc2108-lcb-judge:v1")
        record["cases"].append({"label": label, "expected": expected, "evaluation": evaluation})
        write_json(root / "result.json", record)
        print(json.dumps(record["cases"][-1]))
        if evaluation["status"] != expected:
            raise RuntimeError(f"Judge validation failed for {label}")
    record["status"] = "pass"
    write_json(root / "result.json", record)
    print(json.dumps({"output": str(root), "status": "pass"}))


if __name__ == "__main__":
    main()
