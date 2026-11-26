"""CLI entrypoint for enhanced_de experiments."""
import argparse
import json
import sys
from pathlib import Path

from guided_agent.common import read_json

from . import runner_v2


def main(argv=None):
    p = argparse.ArgumentParser(prog='python -m enhanced_de')
    sub = p.add_subparsers(dest='cmd', required=True)

    p_one = sub.add_parser('run-one', help='Run one attempt from a spec JSON file')
    p_one.add_argument('spec', type=Path)

    p_eval = sub.add_parser('evaluate', help='Run hidden evaluation on a batch directory')
    p_eval.add_argument('batch_dir', type=Path)
    p_eval.add_argument('--study', type=Path, required=True)

    args = p.parse_args(argv)
    if args.cmd == 'run-one':
        spec = read_json(args.spec)
        rec = runner_v2.run_enhanced_attempt(spec)
        print(json.dumps({
            'run_id': rec.get('run_id'),
            'arm': rec.get('arm'),
            'exit_status': rec.get('exit_status'),
            'n_actions': rec.get('n_actions'),
            'wall_seconds': rec.get('wall_seconds'),
            'submission_sha256': rec.get('submission_sha256'),
        }), flush=True)
        return 0
    if args.cmd == 'evaluate':
        res = runner_v2.evaluate_batch_v2(args.batch_dir, args.study)
        passes = sum(1 for v in res.values() if v.get('status') == 'pass')
        print(f'Evaluated {len(res)} runs: {passes} hidden passes', flush=True)
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main())
