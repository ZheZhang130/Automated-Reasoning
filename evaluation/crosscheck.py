"""Bounded cross-validation of judge 0.2.1 against the official LiveCodeBench evaluator on saved submissions.

No model is run. For up to ``limit`` hidden-scored runs (alternating passes and failures, in a fixed order), the saved
``submission.py`` is re-judged by the official evaluator (``lcb_runner`` at the pinned evaluator revision
``local_agent.cli.EVALUATOR_REVISION``) through the frozen wrapper ``local_baseline/judge_lcb.py``, inside the same
disposable container the earlier studies used: image ``csc2108-lcb-judge:v2``, no network, read-only root, 1 GB,
1 CPU, 64 pids, unprivileged user, all capabilities dropped, the evaluator source mounted read-only.

Only the *hidden* (private) tests are passed to the official evaluator (``public_test_cases`` is emptied), so both
evaluators judge the same cases. Agreement does not remove the limitation both share: exact output comparison is
only valid for tasks with one acceptable output (see ``evaluation/data/output-semantics-audit.json``).
"""
import json
import subprocess
import uuid
from pathlib import Path

from .plan import read_json, write_json
from .tasks import REPO, build_data, locate_shard

WRAPPER = REPO / 'local_baseline/judge_lcb.py'   # frozen (one of the 38 verified files); mounted read-only, unchanged


def _vendor(path=None):
    from local_agent.cli import EVALUATOR_REVISION, VENDOR
    vendor = Path(path) if path else VENDOR
    head = subprocess.run(['git', '-C', str(vendor), 'rev-parse', 'HEAD'], capture_output=True, text=True)
    dirty = subprocess.run(['git', '-C', str(vendor), 'status', '--porcelain'], capture_output=True, text=True)
    if head.returncode or head.stdout.strip() != EVALUATOR_REVISION or dirty.stdout.strip():
        raise RuntimeError(f'{vendor} must be a clean LiveCodeBench checkout at {EVALUATOR_REVISION}')
    return vendor, EVALUATOR_REVISION


def official(source, row, vendor, image, timeout=600):
    """The official evaluator's verdict on the hidden tests of ``row`` (stdin tasks only)."""
    hidden_only = dict(row, public_test_cases='[]')
    name = 'csc2108-lcb-xcheck-' + uuid.uuid4().hex[:12]
    command = ['docker', 'run', '--name', name, '--rm', '--pull', 'never', '-i', '--network', 'none', '--read-only',
               '--memory', '1g', '--memory-swap', '1g', '--cpus', '1', '--pids-limit', '64', '--user', '65534:65534',
               '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
               '--tmpfs', '/tmp:rw,nosuid,size=128m,mode=1777',
               '--mount', f'type=bind,src={vendor},dst=/opt/lcb,readonly',
               '--mount', f'type=bind,src={WRAPPER},dst=/judge.py,readonly',
               image, 'python', '-I', '/judge.py']
    try:
        proc = subprocess.run(command, input=json.dumps({'source': source, 'row': hidden_only}), capture_output=True,
                              text=True, encoding='utf-8', timeout=timeout)
        lines = [x for x in proc.stdout.splitlines() if x.startswith('CSC2108_EVALUATION=')]
        if not lines:
            return {'status': 'infrastructure_error', 'error': (proc.stderr or proc.stdout)[-500:]}
        result = json.loads(lines[-1].split('=', 1)[1])
        flat = (result.get('results') or [[]])[0]
        return {'status': result['status'], 'passed': sum(x is True or x == 1 for x in flat), 'total': len(flat),
                'metadata': (result.get('metadata') or [None])[0]}
    except subprocess.TimeoutExpired:
        return {'status': 'infrastructure_error', 'error': f'no result within {timeout} s'}
    finally:
        subprocess.run(['docker', 'rm', '-f', name], capture_output=True)


def candidates(batches, limit):
    """Hidden-scored runs with a submission: alternating pass / failure, then by (task, run) for a fixed order."""
    found = {'pass': [], 'candidate_failure': []}
    for batch in map(Path, batches):
        for verdict_path in sorted((batch / 'eval').glob('*.json')):
            verdict = read_json(verdict_path)
            if verdict.get('status') not in found:
                continue
            for run_dir in batch.iterdir():
                result = run_dir / 'result.json'
                if result.exists() and (run_dir / 'submission.py').exists():
                    record = read_json(result)
                    if record.get('run_id') == verdict.get('run_id'):
                        found[verdict['status']].append((record['task_id'], run_dir, verdict))
                        break
    for key in found:
        found[key].sort(key=lambda x: (x[0], x[1].name))
    picked, i = [], 0
    while len(picked) < limit and (i < len(found['pass']) or i < len(found['candidate_failure'])):
        for key in ('pass', 'candidate_failure'):
            if i < len(found[key]) and len(picked) < limit:
                picked.append(found[key][i])
        i += 1
    return picked


def run(batches, *, out, study=None, shard=None, limit=40, image='csc2108-lcb-judge:v2', vendor=None):
    vendor, revision = _vendor(vendor)
    bd = build_data()
    shard_path = locate_shard(bd, '0fe84c3912ea0c4d4a78037083943e8f0c4dd505', shard)
    picked = candidates(batches, limit)
    wanted = {t for t, _, _ in picked}
    rows = {}
    with Path(shard_path).open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            task_id = f"lcb-{row['platform']}-{row['question_id']}"
            if task_id in wanted:
                rows[task_id] = row
    results = []
    for task_id, run_dir, ours in picked:
        if task_id not in rows:
            results.append({'task_id': task_id, 'run': run_dir.name, 'skipped': 'not in the pinned shard'})
            continue
        theirs = official((run_dir / 'submission.py').read_text(encoding='utf-8'), rows[task_id], vendor, image)
        results.append({'task_id': task_id, 'run': f'{run_dir.parent.name}/{run_dir.name}',
                        'ours': {k: ours.get(k) for k in ('status', 'passed', 'total')},
                        'official': {k: theirs.get(k) for k in ('status', 'passed', 'total', 'error')},
                        'official_first_failure': theirs.get('metadata'),
                        'agree': ours.get('status') == theirs.get('status')})
    compared = [r for r in results if 'agree' in r and r['official']['status'] != 'infrastructure_error']
    summary = {'schema': 'csc2108-judge-crosscheck-v1', 'evaluator_revision': revision, 'image': image,
               'judged_suite': 'hidden (private) tests only, for both evaluators',
               'runs': len(results), 'compared': len(compared), 'agree': sum(r['agree'] for r in compared),
               'disagree': [r for r in compared if not r['agree']],
               'official_infrastructure_errors': sum(1 for r in results if (r.get('official') or {}).get('status')
                                                     == 'infrastructure_error'),
               'by_our_status': {s: sum(1 for r in compared if r['ours']['status'] == s) for s in ('pass', 'candidate_failure')},
               'results': results,
               'limitation': 'agreement does not cover tasks with several acceptable outputs; both evaluators compare '
                             'exactly (stripped lines, Decimal-equal numbers)'}
    write_json(Path(out) / 'crosscheck.json', summary)
    return {k: v for k, v in summary.items() if k != 'results'}
