"""Public-only LiveCodeBench development feedback; official scoring is separate."""
import json
import subprocess
from pathlib import Path

cases = json.loads(Path("/public/public_tests.json").read_text())
for index, case in enumerate(cases, 1):
    result = subprocess.run(["python", "-I", "/workspace/solution.py"], input=case["input"],
                            text=True, capture_output=True, timeout=5)
    if result.returncode or result.stdout.split() != case["output"].split():
        print(json.dumps({"case": index, "status": "candidate_failure", "input": case["input"],
                          "expected": case["output"], "actual": result.stdout[:2000],
                          "stderr": result.stderr[:2000], "returncode": result.returncode}))
        raise SystemExit(1)
print(json.dumps({"status": "pass", "cases": len(cases), "comparison": "whitespace tokens"}))
