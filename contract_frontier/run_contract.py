"""Run one upfront contract then the shared mini-SWE-agent coding loop."""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
# The shared runner retains its script entry point and original planning imports.
sys.path.insert(0, str(REPO / "planning_frontier"))
from plan_once import run
from contract_frontier.contracts import (
    SavedContract, FrontierContract, OllamaContract, generate_contract,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--local-model", default="qwen3.5:9b")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11435")
    parser.add_argument("--context", type=int, default=16384)
    parser.add_argument("--coding-tokens", type=int, default=4000)
    parser.add_argument("--seconds", type=int, default=600)
    parser.add_argument("--contract-context", type=int, default=8192)
    parser.add_argument("--contract-tokens", type=int, default=2000)
    parser.add_argument("--contract-timeout", type=int, default=180)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--contract-file", type=Path)
    source.add_argument("--frontier-model")
    source.add_argument("--local-contract-smoke", action="store_true")
    args = parser.parse_args()
    if args.contract_file:
        provider = SavedContract(args.contract_file)
    elif args.frontier_model:
        provider = FrontierContract(args.frontier_model, args.contract_tokens)
    else:
        provider = OllamaContract(args.endpoint, args.local_model,
                                  args.contract_context, args.contract_tokens)
    result = run(REPO, args.task, args.output, provider, args.local_model,
                 args.endpoint, args.context, args.seconds, args.contract_timeout,
                 args.coding_tokens, guidance_kind="contract",
                 guidance_generator=generate_contract)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
