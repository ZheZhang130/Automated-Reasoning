"""guided_agent command line (identical on Windows PowerShell and POSIX shells).

  python -m guided_agent prepare-tasks --ids lcb-atcoder-abc394_b ...
  python -m guided_agent prepare-fixture                      # synthetic signed-sum smoke task
  python -m guided_agent author --provider codex --prompt-id plan-v1 --tasks ... --label dev
  python -m guided_agent author --provider api --prompt-id contract-v1 --tasks ... --purpose ...
  python -m guided_agent batch PLAN.json                      # sequential attempts under the GPU lock
  python -m guided_agent evaluate BATCH_DIR                   # hidden judge, after all attempts
  python -m guided_agent summarize BATCH_DIR
"""
import argparse
import concurrent.futures
import json
import shutil
import sys
import uuid
from pathlib import Path

from .common import CONDITIONS, REPO, read_json, settings, study_root, utc_now, write_json


def cmd_prepare_tasks(args, host, study):
    from .tasks import prepare
    record = prepare(args.ids, study, host, shard=args.shard)
    print(json.dumps({k: {f: v[f] for f in ('difficulty', 'n_public', 'n_hidden', 'manifest')}
                      for k, v in record['tasks'].items() if k in args.ids}, indent=1))


def cmd_prepare_fixture(args, host, study):
    """Copy Peter's synthetic judge fixture; it exercises the full path without LiveCodeBench data."""
    source = REPO / 'judge/tests/fixtures'
    task_id = 'fixture-sum-signed'
    shutil.copytree(source / 'tasks' / task_id, study / 'judge/tasks' / task_id)
    shutil.copytree(source / 'hidden' / task_id, study / 'judge/hidden' / task_id)
    meta = read_json(source / 'tasks' / task_id / 'task.json')
    statement = (source / 'tasks' / task_id / 'problem.md').read_text(encoding='utf-8') \
        if (source / 'tasks' / task_id / 'problem.md').exists() else \
        'Read two signed integers A and B from standard input and print A + B.\n'
    from .tasks import CHECK_STUB
    bundle = study / 'bundles' / task_id
    bundle.mkdir(parents=True)
    write_json(bundle / 'task.json', {'task_id': task_id, 'version': '1', 'statement': statement,
                                      'submission_path': 'solution.py'})
    cases = []
    for case in sorted((source / 'tasks' / task_id / 'tests/public').glob('*.in')):
        cases.append({'input': case.read_text(encoding='utf-8'),
                      'output': case.with_suffix('.out').read_text(encoding='utf-8'), 'testtype': 'stdin'})
    write_json(bundle / 'public_tests.json', cases)
    (bundle / 'check.py').write_text(CHECK_STUB, encoding='utf-8', newline='\n')
    print(json.dumps({'task_id': task_id, 'meta': meta, 'bundle': str(bundle)}))


def cmd_author(args, host, study):
    from . import guidance, providers
    from .tasks import load_statement
    kind = guidance.PROMPTS[args.prompt_id][0]
    out_dir = study / 'guidance' / args.label
    out_dir.mkdir(parents=True, exist_ok=True)

    def one(task_id):
        out = out_dir / f'{task_id}.{args.prompt_id}.{args.provider}.json'
        statement = load_statement(study, task_id)
        if args.provider == 'codex':
            record = providers.codex_author(kind=kind, prompt_id=args.prompt_id, statement=statement, task_id=task_id,
                                            out_path=out, work_root=study / 'codex-work', model=args.model,
                                            effort=args.effort, label=args.label)
        else:
            record = providers.api_author(kind=kind, prompt_id=args.prompt_id, statement=statement, task_id=task_id,
                                          out_path=out, ledger_path=study / 'api-ledger.json', effort=args.effort,
                                          max_completion_tokens=args.max_completion_tokens, label=args.label,
                                          purpose=args.purpose)
        return task_id, str(out), record['word_count'], record['validation_problems']

    workers = args.parallel if args.provider == 'codex' else 1  # paid calls stay sequential
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(one, t): t for t in args.tasks}
        for future in concurrent.futures.as_completed(futures):
            try:
                print(json.dumps(future.result()), flush=True)
            except Exception as error:
                print(json.dumps({'task_id': futures[future], 'error': f'{type(error).__name__}: {error}'}), flush=True)


def cmd_run_one(args, host, study):
    from .runner import run_attempt
    record = run_attempt(read_json(args.spec))
    print(json.dumps({k: record.get(k) for k in ('run_id', 'task_id', 'condition', 'exit_status', 'raw_exit_status',
                                                 'n_actions', 'n_repairs', 'wall_seconds', 'setup_error')}))


def foreign_models(url='http://127.0.0.1:11434/api/ps'):
    """Models loaded by the user's own Ollama app endpoint (never unloaded by us)."""
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return [m.get('name') for m in json.load(response).get('models', [])]
    except Exception:
        return []


def wait_for_gpu(max_wait=7200, poll=30):
    """The frozen runtime refuses to start while another workload holds a model; wait politely instead."""
    import time
    waited = 0
    while (loaded := foreign_models()) and waited < max_wait:
        if waited % 300 == 0:
            print(json.dumps({'waiting_for_foreign_models': loaded, 'waited_seconds': waited, 'utc': utc_now()}),
                  flush=True)
        time.sleep(poll)
        waited += poll
    return waited


def cmd_batch(args, host, study):
    from .runner import run_child
    plan = read_json(args.plan)
    batch_dir = study / 'runs' / plan['batch']
    batch_dir.mkdir(parents=True, exist_ok=True)
    write_json(batch_dir / 'plan.json', plan | {'plan_path': str(args.plan)})
    for item in plan['attempts']:
        if item['condition'] not in CONDITIONS:
            raise ValueError('Unsupported condition ' + item['condition'])
        name = f"{item['task_id']}-{item['condition']}" + (f"-{item['variant']}" if item.get('variant') else '')
        out = batch_dir / name
        if (out / 'result.json').exists():
            continue
        if out.exists():  # interrupted earlier: keep evidence, retry under a new directory name
            out.rename(batch_dir / f'{name}.incomplete-{uuid.uuid4().hex[:6]}')
        spec = {'backend': args.backend} | item | {
            'run_id': f"{plan['batch']}-{name}-{uuid.uuid4().hex[:8]}", 'output': str(out),
            'batch': plan['batch'], 'cohort': plan.get('cohort'), 'study': str(study)}
        if not item.get('coder') and host.backend == 'windows':
            wait_for_gpu()
        timeout = plan.get('outer_timeout', 960)
        if item['condition'] == 'E':  # the supervisor also covers the (separately accounted) frontier wait
            timeout += int((item.get('diagnosis') or {}).get('timeout', 300)) + 30
        record = run_child(spec, timeout)
        print(json.dumps({k: record.get(k) for k in ('run_id', 'exit_status', 'raw_exit_status', 'n_actions',
                                                     'n_repairs', 'wall_seconds', 'setup_error')}), flush=True)


def cmd_evaluate(args, host, study):
    from .runner import evaluate
    results = evaluate(Path(args.batch), study)
    print(json.dumps({k: v['status'] for k, v in results.items()}, indent=1))


def cmd_summarize(args, host, study):
    from .analysis import summarize
    summary = summarize(Path(args.batch))
    print(json.dumps(summary['table'], indent=1))


def main(argv=None):
    parser = argparse.ArgumentParser(prog='guided_agent', description=__doc__.splitlines()[0])
    parser.add_argument('--backend', default='auto', choices=['auto', 'windows', 'portable'])
    parser.add_argument('--study', help='Study root (default <data root>/reasoning-effectiveness)')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare-tasks'); p.add_argument('--ids', nargs='+', required=True); p.add_argument('--shard')
    sub.add_parser('prepare-fixture')
    p = sub.add_parser('author')
    p.add_argument('--provider', choices=['codex', 'api'], required=True)
    p.add_argument('--prompt-id', required=True)
    p.add_argument('--tasks', nargs='+', required=True)
    p.add_argument('--label', required=True)
    p.add_argument('--model', default='gpt-6.2-sol')
    p.add_argument('--effort', default='medium')
    p.add_argument('--parallel', type=int, default=3)
    p.add_argument('--max-completion-tokens', type=int, default=8000)
    p.add_argument('--purpose', default='')
    p = sub.add_parser('run-one'); p.add_argument('spec')
    p = sub.add_parser('batch'); p.add_argument('plan')
    p = sub.add_parser('evaluate'); p.add_argument('batch')
    p = sub.add_parser('summarize'); p.add_argument('batch')
    args = parser.parse_args(argv)
    host = settings(args.backend)
    study = study_root(host, args.study)
    if args.command == 'author' and args.provider == 'api' and not args.purpose:
        parser.error('--purpose is required for paid API requests')
    globals()['cmd_' + args.command.replace('-', '_')](args, host, study)


if __name__ == '__main__':
    sys.exit(main())
