"""E mechanism probe: original continuation vs diagnosis-v1 vs neutral message vs diagnosis-v2 at 11 frozen states.

usage: python reasoning_effectiveness/pass4/diagnostics/e_probe_analysis.py OUT.json

A state counts only if the pass-4 run's trigger packet candidate hash equals the historical one (the frozen agent at
the same seed must reproduce the trajectory up to the trigger). Historical arms: A (same task and seed, original
agent) and diagnosis-v1 (pass 2/3 Codex), neutral for pass-2 states (pass-3 probe). New arms: neutral for pass-3
states and diagnosis-v2 (pass 4).
"""
import json
import sys
from pathlib import Path

D = Path('E:/CSC2108Local')
P2 = D / 'reasoning-effectiveness-pass2/runs'
P3 = D / 'reasoning-effectiveness-pass3/runs'
P4 = D / 'reasoning-effectiveness-pass4/runs/p4-eprobe'
P1 = D / 'reasoning-effectiveness/runs'
STATES = {  # state: (A run dir, E-v1 run dir, neutral run dir or None)
    ('abc390_c', 2108): (P1 / 'mb1/lcb-atcoder-abc390_c-A', P2 / 'dev-e/lcb-atcoder-abc390_c-E', P3 / 'probe-neutral/lcb-atcoder-abc390_c-E-neutral-s2108'),
    ('abc393_d', 2108): (P2 / 'dev-d/lcb-atcoder-abc393_d-A', P2 / 'dev-e/lcb-atcoder-abc393_d-E', P3 / 'probe-neutral/lcb-atcoder-abc393_d-E-neutral-s2108'),
    ('abc398_d', 2108): (P2 / 'val/lcb-atcoder-abc398_d-A', P2 / 'val/lcb-atcoder-abc398_d-E', P3 / 'probe-neutral/lcb-atcoder-abc398_d-E-neutral-s2108'),
    ('arc195_a', 2108): (P2 / 'dev-d/lcb-atcoder-arc195_a-A', P2 / 'dev-e/lcb-atcoder-arc195_a-E', P3 / 'probe-neutral/lcb-atcoder-arc195_a-E-neutral-s2108'),
    ('arc195_a', 2109): (P1 / 'dev2/lcb-atcoder-arc195_a-A-s2109', P2 / 'dev-s2109/lcb-atcoder-arc195_a-E-s2109', P3 / 'probe-neutral/lcb-atcoder-arc195_a-E-neutral-s2109'),
    ('abc390_f', 2108): (P3 / 'ext-s2108/lcb-atcoder-abc390_f-A', P3 / 'ext-s2108/lcb-atcoder-abc390_f-E', None),
    ('abc395_f', 2108): (P3 / 'ext-s2108/lcb-atcoder-abc395_f-A', P3 / 'ext-s2108/lcb-atcoder-abc395_f-E', None),
    ('abc388_f', 2109): (P3 / 'ext-s2109/lcb-atcoder-abc388_f-A', P3 / 'ext-s2109/lcb-atcoder-abc388_f-E', None),
    ('abc395_f', 2109): (P3 / 'ext-s2109/lcb-atcoder-abc395_f-A', P3 / 'ext-s2109/lcb-atcoder-abc395_f-E', None),
    ('arc190_c', 2109): (P3 / 'ext-s2109/lcb-atcoder-arc190_c-A', P3 / 'ext-s2109/lcb-atcoder-arc190_c-E', None),
    ('arc193_a', 2109): (P3 / 'ext-s2109/lcb-atcoder-arc193_a-A', P3 / 'ext-s2109/lcb-atcoder-arc193_a-E', None),
}


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def outcome(run_dir):
    if run_dir is None or not (Path(run_dir) / 'result.json').exists():
        return None
    record = load(Path(run_dir) / 'result.json')
    hidden_path = Path(run_dir).parent / 'eval' / f"{record['run_id']}.json"
    hidden = load(hidden_path) if hidden_path.exists() else {}
    d = record.get('diagnosis') or {}
    packet = d.get('packet') or {}
    return {'run': str(Path(run_dir).relative_to(D)), 'hidden': hidden.get('status'), 'hidden_passed': hidden.get('passed'),
            'exit': record.get('exit_status'), 'trigger': d.get('trigger_observed'), 'delivered': d.get('delivered'),
            'candidate': packet.get('candidate_sha256'), 'public_pass_after': d.get('public_pass_after'),
            'candidate_changed_after': d.get('candidate_changed_after'), 'local_actions_after': d.get('local_actions_after'),
            'wait': d.get('frontier_wait_seconds'), 'words': d.get('diagnosis_words'), 'error': d.get('error_category')}


def main(out):
    rows = []
    for (task, seed), (a_dir, e1_dir, neutral_dir) in STATES.items():
        e1 = outcome(e1_dir)
        new_neutral = outcome(P4 / f'lcb-atcoder-{task}-E-neutral-s{seed}')
        v2 = outcome(P4 / f'lcb-atcoder-{task}-E-dv2-s{seed}')
        neutral = outcome(neutral_dir) if neutral_dir else new_neutral
        historical = e1['candidate'] if e1 else None
        reproduced = {name: (x or {}).get('candidate') == historical for name, x in (('neutral', neutral), ('v2', v2))}
        rows.append({'state': f'{task} s{seed}', 'historical_candidate': historical, 'reproduced': reproduced,
                     'A': outcome(a_dir), 'v1': e1, 'neutral': neutral, 'v2': v2,
                     'neutral_source': 'pass-3 probe' if neutral_dir else 'pass-4 probe'})
    counts = {}
    for arm in ('A', 'v1', 'neutral', 'v2'):
        valid = [r for r in rows if r[arm] and (arm in ('A', 'v1') or r['reproduced'].get(arm))]
        counts[arm] = {'states': len(valid), 'hidden_pass': sum(r[arm]['hidden'] == 'pass' for r in valid),
                       'public_pass_after': sum(bool(r[arm].get('public_pass_after')) for r in valid if arm != 'A')}
    report = {'counts': counts, 'states': rows}
    Path(out).write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(counts))
    for r in rows:
        cells = []
        for arm in ('A', 'v1', 'neutral', 'v2'):
            x = r[arm] or {}
            ok = '' if arm in ('A', 'v1') else ('' if r['reproduced'].get(arm) else ' [NOT REPRODUCED]')
            cells.append(f"{arm}={x.get('hidden')}:{x.get('hidden_passed')}{ok}")
        print(r['state'], ' '.join(cells))


if __name__ == '__main__':
    main(*sys.argv[1:])
