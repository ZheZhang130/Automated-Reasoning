"""Run only in the offline judge container, after the agent has terminated."""
import base64
import io
import json
import pickle
import sys
import zlib

# -I deliberately ignores PYTHONPATH. Add only the pinned, read-only official source.
sys.path.insert(0, "/opt/lcb")
from lcb_runner.evaluation.compute_code_generation_metrics import evaluate_generations_by_problem


class DataOnlyUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        raise ValueError("Dataset pickle may contain only primitive data")


def main():
    payload = json.load(sys.stdin)
    row = payload["row"]
    try:
        private = json.loads(row["private_test_cases"])
    except json.JSONDecodeError:
        packed = zlib.decompress(base64.b64decode(row["private_test_cases"]))
        private = json.loads(DataOnlyUnpickler(io.BytesIO(packed)).load())
    tests = json.loads(row["public_test_cases"]) + private
    sample = {"input_output": json.dumps({"inputs": [t["input"] for t in tests],
              "outputs": [t["output"] for t in tests],
              "fn_name": json.loads(row["metadata"]).get("func_name")})}
    # The official evaluator executes untrusted submissions inside THIS disposable container.
    results, metadata = evaluate_generations_by_problem(([payload["source"]], sample, False, 6))
    status = "pass" if results and results[0] and all(x is True or x == 1 for x in results[0]) else "candidate_failure"
    if any(m.get("error_code") == -5 for m in metadata):
        status = "infrastructure_error"
    print("CSC2108_EVALUATION=" + json.dumps({"status": status, "results": results, "metadata": metadata}))


if __name__ == "__main__":
    main()
