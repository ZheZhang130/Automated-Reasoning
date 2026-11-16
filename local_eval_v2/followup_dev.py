"""Additional pre-benchmark development conditions; all outputs remain distinct."""
import json
import argparse
import subprocess
import sys
from pathlib import Path
from common import DATA, MODELS, ROOT, read, save
from pilot import score


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--common-sampler', action='store_true')
    args = parser.parse_args()
    root = DATA / ('development-common-v6' if args.common_sampler else 'development-secondary')
    tasks = [t['task_id'] for t in read(DATA / 'development-v5/manifest.json')['tasks']]
    profile = 'heredoc-v6-16k-common' if args.common_sampler else 'heredoc-v5-16k-t02'
    jobs = [(m, profile, t, 20, 3) for m in MODELS for t in tasks]
    if not args.common_sampler:
        jobs += [(m, 'heredoc-v5-16k', tasks[0], 40, 5) for m in MODELS]
        jobs += [(m, 'native-v6-16k', tasks[0], 20, 3) for m in MODELS]
    for model, profile, task, actions, repairs in jobs:
        run = root / (model.replace(':', '_') + '--' + profile + '--' + task + '--a' + str(actions))
        if (run / 'development-result.json').exists():
            continue
        if not (run / 'result.json').exists():
            if run.exists():
                raise RuntimeError('Preserve and inspect incomplete secondary attempt: ' + str(run))
            command = [sys.executable, str(ROOT / 'runtime.py'), '--task', str(DATA / 'development-v5/public' / task),
                       '--output', str(run), '--model', model, '--profile', profile, '--actions', str(actions),
                       '--repairs', str(repairs), '--seconds', '240']
            child = subprocess.run(command, capture_output=True, text=True, timeout=330)
            if not (run / 'result.json').exists():
                raise RuntimeError(child.stderr[-2000:])
        result = read(run / 'result.json')
        if args.common_sampler and not result.get('sampler_wire_verified'):
            raise RuntimeError('Common sampler was not verified on the wire: ' + str(run))
        evaluation = score(run, DATA / 'development-v5/private' / (task + '.json'), Path('E:/CSC2108Local/vendor/LiveCodeBench'), 'csc2108-lcb-judge:v1')
        row = {'model': model, 'profile': profile, 'task_id': task, 'actions_limit': actions, 'repair_limit': repairs,
               'status': result['status'], 'evaluation': evaluation, 'seconds': result['elapsed_seconds'],
               'actions': result['actions'], 'repairs': result['repairs'], 'format_errors': result.get('format_errors', 0),
               'inference': result.get('inference'), 'run': str(run)}
        save(run / 'development-result.json', row)
        print(json.dumps({k: row[k] for k in ('model', 'profile', 'task_id', 'actions_limit', 'seconds', 'actions', 'format_errors')} |
                         {'correct': evaluation['status']}), flush=True)


if __name__ == '__main__':
    main()
