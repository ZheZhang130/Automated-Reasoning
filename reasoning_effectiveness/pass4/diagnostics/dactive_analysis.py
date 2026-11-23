"""D-active analysis: per arm hidden outcome, and for executed checks what they showed and what the agent did next.

usage: python reasoning_effectiveness/pass4/diagnostics/dactive_analysis.py OUT.json BATCH_DIR [BATCH_DIR ...]

References (historical, original agent, seed 2108): A and D-v1 for the same 8 tasks.
"""
import json
import sys
from pathlib import Path

D = Path('E:/CSC2108Local')
HIST = {  # task: (A run dir, D-v1 run dir)
    'abc400_b': ('reasoning-effectiveness/runs/dev1-A/lcb-atcoder-abc400_b-A', 'reasoning-effectiveness/runs/dev1-CD/lcb-atcoder-abc400_b-D'),
    'abc393_d': ('reasoning-effectiveness-pass2/runs/dev-d/lcb-atcoder-abc393_d-A', 'reasoning-effectiveness-pass2/runs/dev-d/lcb-atcoder-abc393_d-D-v1codex'),
    'arc195_a': ('reasoning-effectiveness-pass2/runs/dev-d/lcb-atcoder-arc195_a-A', 'reasoning-effectiveness/runs/dev1-CD/lcb-atcoder-arc195_a-D'),
    'abc398_d': ('reasoning-effectiveness-pass2/runs/val/lcb-atcoder-abc398_d-A', 'reasoning-effectiveness-pass2/runs/val/lcb-atcoder-abc398_d-D-v1'),
    'abc388_e': ('reasoning-effectiveness-pass2/runs/val/lcb-atcoder-abc388_e-A', 'reasoning-effectiveness-pass2/runs/val/lcb-atcoder-abc388_e-D-v1'),
    'abc389_f': ('reasoning-effectiveness-pass3/runs/ext-s2108/lcb-atcoder-abc389_f-A', 'reasoning-effectiveness-pass3/runs/ext-s2108/lcb-atcoder-abc389_f-D'),
    'abc397_f': ('reasoning-effectiveness-pass3/runs/ext-s2108/lcb-atcoder-abc397_f-A', 'reasoning-effectiveness-pass3/runs/ext-s2108/lcb-atcoder-abc397_f-D'),
    'arc192_a': ('reasoning-effectiveness/runs/dev1-A/lcb-atcoder-arc192_a-A', 'reasoning-effectiveness/runs/dev1-CD/lcb-atcoder-arc192_a-D'),
}


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def hidden(run_dir):
    run_dir = Path(run_dir)
    if not (run_dir / 'result.json').exists():
        return None
    record = load(run_dir / 'result.json')
    path = run_dir.parent / 'eval' / f"{record['run_id']}.json"
    return load(path).get('status') if path.exists() else None


def run_metrics(run_dir):
    record = load(run_dir / 'result.json')
    agent_dir = run_dir / ('agent-' + record['run_id'])
    events = [e for e in (load(agent_dir / 'result.json').get('events') or []) if 'command' in e]
    tests = [e for e in events if e.get('recognized_public_test')]
    executed = [e for e in tests if (e.get('contract_checks') or {}).get('results')]
    flagged = [e for e in executed if any(r['outcome'] != 'same' and r['outcome'] != 'ran' for r in e['contract_checks']['results'])]
    acted = 0
    for e in flagged:
        later = [x for x in events if x['action'] > e['action']]
        acted += any(x.get('source_sha256') not in (None, e.get('source_sha256')) for x in later)
    public_pass_flagged = [e for e in flagged if e.get('public_status') == 'pass']
    return {'run': run_dir.name, 'hidden': hidden(run_dir), 'exit': record.get('exit_status'),
            'program': record.get('submission_sha256') is not None, 'actions': record.get('n_actions'),
            'public_tests': len(tests), 'tests_with_checks': len(executed),
            'tests_with_a_difference': len(flagged), 'differences_followed_by_an_edit': acted,
            'public_pass_but_check_difference': len(public_pass_flagged),
            'check_seconds': round(sum((e.get('contract_checks') or {}).get('seconds', 0) for e in tests), 3),
            'final_check_outcomes': (record.get('contract_checks_summary') or {}).get('final_outcomes'),
            'wall_seconds': record.get('wall_seconds'),
            'output_tokens': (record.get('inference') or {}).get('eval_count')}


def main(out, *batches):
    rows = {}
    for batch in batches:
        for result in sorted(Path(batch).glob('*/result.json')):
            name = result.parent.name
            task = name.split('-')[2]
            arm = name.split('-D-')[1] if '-D-' in name else name.split('-')[-2]
            rows.setdefault(task, {})[arm] = run_metrics(result.parent)
    for task, (a_dir, d_dir) in HIST.items():
        rows.setdefault(task, {})['A (hist)'] = {'hidden': hidden(D / a_dir)}
        rows[task]['D-v1 (hist)'] = {'hidden': hidden(D / d_dir)}
    arms = sorted({arm for v in rows.values() for arm in v})
    totals = {arm: sum((rows[t].get(arm) or {}).get('hidden') == 'pass' for t in rows) for arm in arms}
    Path(out).write_text(json.dumps({'totals': totals, 'rows': rows}, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(totals))
    for task in rows:
        print(task, {arm: (rows[task].get(arm) or {}).get('hidden') for arm in arms})
        for arm, m in rows[task].items():
            if 'tests_with_checks' in m and m['tests_with_checks']:
                print('   ', arm, {k: m[k] for k in ('tests_with_checks', 'tests_with_a_difference', 'differences_followed_by_an_edit',
                                                     'public_pass_but_check_difference', 'final_check_outcomes', 'check_seconds')})


if __name__ == '__main__':
    main(*sys.argv[1:])
