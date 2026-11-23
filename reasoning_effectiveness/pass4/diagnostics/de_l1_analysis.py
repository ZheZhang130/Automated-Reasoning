"""D-v1 and E (diagnosis-v1) under l1-selfplan-v1 against the historical frozen-agent runs (seed 2108).

usage: python reasoning_effectiveness/pass4/diagnostics/de_l1_analysis.py OUT.json
"""
import json
import sys
from pathlib import Path

D = Path('E:/CSC2108Local')
NEW = D / 'reasoning-effectiveness-pass4/runs/p4-stageD-de'
HIST_D = {'abc400_b': 'reasoning-effectiveness/runs/dev1-CD/lcb-atcoder-abc400_b-D',
          'abc393_d': 'reasoning-effectiveness-pass2/runs/dev-d/lcb-atcoder-abc393_d-D-v1codex',
          'arc195_a': 'reasoning-effectiveness/runs/dev1-CD/lcb-atcoder-arc195_a-D',
          'abc398_d': 'reasoning-effectiveness-pass2/runs/val/lcb-atcoder-abc398_d-D-v1',
          'abc388_e': 'reasoning-effectiveness-pass2/runs/val/lcb-atcoder-abc388_e-D-v1',
          'abc389_f': 'reasoning-effectiveness-pass3/runs/ext-s2108/lcb-atcoder-abc389_f-D',
          'abc397_f': 'reasoning-effectiveness-pass3/runs/ext-s2108/lcb-atcoder-abc397_f-D',
          'arc192_a': 'reasoning-effectiveness/runs/dev1-CD/lcb-atcoder-arc192_a-D'}
HIST_E = {'abc393_d': 'reasoning-effectiveness-pass2/runs/dev-e/lcb-atcoder-abc393_d-E',
          'arc195_a': 'reasoning-effectiveness-pass2/runs/dev-e/lcb-atcoder-arc195_a-E',
          'abc398_d': 'reasoning-effectiveness-pass2/runs/val/lcb-atcoder-abc398_d-E',
          'abc388_e': 'reasoning-effectiveness-pass2/runs/val/lcb-atcoder-abc388_e-E',
          'abc389_f': 'reasoning-effectiveness-pass3/runs/ext-s2108/lcb-atcoder-abc389_f-E',
          'abc397_f': 'reasoning-effectiveness-pass3/runs/ext-s2108/lcb-atcoder-abc397_f-E',
          'arc192_a': 'reasoning-effectiveness-pass2/runs/dev-e/lcb-atcoder-arc192_a-E',
          # abc400_b: no historical frozen E run; an untriggered E is byte-identical to A, so A stands in
          'abc400_b': 'reasoning-effectiveness/runs/dev1-A/lcb-atcoder-abc400_b-A'}


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def outcome(run_dir):
    run_dir = Path(run_dir)
    if not (run_dir / 'result.json').exists():
        return None
    record = load(run_dir / 'result.json')
    hidden_path = run_dir.parent / 'eval' / f"{record['run_id']}.json"
    hidden = load(hidden_path) if hidden_path.exists() else {}
    d = record.get('diagnosis') or {}
    agent_dir = run_dir / ('agent-' + record['run_id'])
    responses = load(agent_dir / 'ollama-responses.json') if (agent_dir / 'ollama-responses.json').exists() else []
    overflow = (record.get('frozen_error') or {}).get('error_type') == 'APIConnectionError' and bool(responses) and \
        (responses[-1].get('prompt_eval_count') or 0) + (responses[-1].get('eval_count') or 0) >= 16384 - 1024
    return {'run': str(run_dir.relative_to(D)), 'hidden': hidden.get('status'), 'hidden_passed': hidden.get('passed'),
            'exit': record.get('exit_status'), 'program': record.get('submission_sha256') is not None,
            'triggered': d.get('trigger_observed'), 'delivered': d.get('delivered'),
            'public_pass_after': d.get('public_pass_after'), 'context_overflow': overflow}


def main(out):
    rows = {}
    for t in HIST_D:
        rows[t] = {'D_frozen': outcome(D / HIST_D[t]), 'D_l1': outcome(NEW / f'lcb-atcoder-{t}-D-l1-v1-s2108'),
                   'E_frozen': outcome(D / HIST_E[t]), 'E_l1': outcome(NEW / f'lcb-atcoder-{t}-E-l1-s2108')}
    totals = {arm: {'hidden_pass': sum((r[arm] or {}).get('hidden') == 'pass' for r in rows.values()),
                    'no_program': sum(not (r[arm] or {}).get('program', False) for r in rows.values()),
                    'triggered': sum(bool((r[arm] or {}).get('triggered')) for r in rows.values()),
                    'overflow': sum(bool((r[arm] or {}).get('context_overflow')) for r in rows.values())}
              for arm in ('D_frozen', 'D_l1', 'E_frozen', 'E_l1')}
    Path(out).write_text(json.dumps({'totals': totals, 'rows': rows}, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(totals))
    for t, r in rows.items():
        print(t, {arm: (f"{(x or {}).get('hidden')}" + (' T' if (x or {}).get('triggered') else '') + (' OVF' if (x or {}).get('context_overflow') else ''))
                  for arm, x in r.items()})


if __name__ == '__main__':
    main(*sys.argv[1:])
