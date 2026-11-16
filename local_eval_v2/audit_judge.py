"""Judge-only reference validation on OLD excluded tasks; never runs an agent."""
import html
import re
import argparse
import uuid
from pathlib import Path
from urllib.request import urlopen

from common import DATA, digest, save
from pilot import score


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--medium-reference', type=Path, required=True, help='Trusted audit-only reference outside every agent public bundle')
    args = parser.parse_args()
    if 'public' in [p.lower() for p in args.medium_reference.parts]:
        raise ValueError('Reference must remain outside agent public bundles')
    root = DATA / "audit" / ('judge-references-' + uuid.uuid4().hex[:8])
    root.mkdir(parents=True, exist_ok=False)
    url = "https://atcoder.jp/contests/abc301/editorial/6368"
    page = urlopen(url, timeout=30).read().decode()
    blocks = [html.unescape(re.sub("<[^>]+>", "", b)) for b in re.findall(r"<pre[^>]*>\s*<code[^>]*>(.*?)</code>\s*</pre>", page, re.S)]
    python = [b for b in blocks if "int(input())" in b and "#include" not in b]
    if len(python) != 1:
        raise ValueError("Cannot identify official Python reference")
    medium = args.medium_reference.read_text(encoding='utf-8')
    results = []
    for task, reference, provenance in [("atcoder-abc301_a", python[0], url),
                                       ("atcoder-abc301_c", medium, "independent audit oracle; https://atcoder.jp/contests/abc301/editorial/6367")]:
        for kind, code in [("reference", reference), ("wrong", "print('JUDGE_WRONG_SENTINEL')\n"), ("syntax", "def broken(\n")]:
            run = root / (task + "-" + kind)
            run.mkdir()
            (run / "solution.py").write_text(code, encoding="utf-8")
            evaluation = score(run, Path("E:/CSC2108Local/lcb-v1/evaluator_private") / (task + ".json"),
                               Path("E:/CSC2108Local/vendor/LiveCodeBench"), "csc2108-lcb-judge:v1")
            expected = "pass" if kind == "reference" else "candidate_failure"
            item = {"task_id": task, "kind": kind, "provenance": provenance, "source_sha256": digest(run / "solution.py"),
                    "expected": expected, "evaluation": evaluation}
            results.append(item)
            save(root / "results.json", results)
            print({"task": task, "kind": kind, "expected": expected, "actual": evaluation['status']}, flush=True)
            if evaluation['status'] != expected:
                raise RuntimeError("Real-task judge audit failed")


if __name__ == "__main__":
    main()
