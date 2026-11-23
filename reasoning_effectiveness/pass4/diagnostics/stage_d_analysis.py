"""Stage D: candidate shared agent vs frozen-v6 for A and C at seeds 2108 and 2109 (pre-registered criteria).

usage: python reasoning_effectiveness/pass4/diagnostics/stage_d_analysis.py OUT.json CANDIDATE

Cells come from pass-4 runs where they exist (screening, stage D) and otherwise from historical original-agent runs
with the identical artifact (C) or the same task and seed (A); the frozen agent reproduces history byte for byte, and
two fresh C-frozen spot checks are compared with their historical twins.
"""
import hashlib
import json
import sys
from pathlib import Path

D = Path('E:/CSC2108Local')
P4 = D / 'reasoning-effectiveness-pass4/runs'
HIST = [D / 'reasoning-effectiveness/runs', D / 'reasoning-effectiveness-pass2/runs', D / 'reasoning-effectiveness-pass3/runs']
TASKS = ['abc400_b', 'abc393_d', 'arc195_a', 'abc398_d', 'abc388_e', 'abc389_f', 'abc397_f', 'arc192_a']
PLANS = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (D / 'reasoning-effectiveness-pass4/guidance/p4-dev-plans').glob('*.json')}


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def outcome(result_path):
    record = load(result_path)
    hidden_path = Path(result_path).parent.parent / 'eval' / f"{record['run_id']}.json"
    hidden = load(hidden_path) if hidden_path.exists() else {}
    inference = record.get('inference') or {}
    sp = record.get('self_plan') or {}
    return {'run': str(Path(result_path).parent.relative_to(D)), 'hidden': hidden.get('status'),
            'hidden_passed': hidden.get('passed'), 'program': record.get('submission_sha256') is not None,
            'submission': record.get('submission_sha256'), 'exit': record.get('exit_status'),
            'output_tokens': (inference.get('eval_count') or 0) + (sp.get('completion_tokens') or 0),
            'wall_seconds': record.get('wall_seconds') or 0.0, 'agent': (record.get('agent_config') or {}).get('id', 'frozen-v6')}


def historical(task, condition, seed):
    for root in HIST:
        for result in root.glob('*/*/result.json'):
            if '.incomplete-' in result.parent.name or 'probe' in result.parent.parent.name:
                continue
            record = load(result)
            if record.get('task_id') != 'lcb-atcoder-' + task or record.get('condition') != condition \
                    or record.get('seed') != seed or record.get('aci') or record.get('coder') or record.get('smoke'):
                continue
            if condition == 'C' and (record.get('guidance_provenance') or {}).get('artifact_sha256') not in PLANS.values():
                continue
            return outcome(result)
    return None


def pass4(batch, name):
    path = P4 / batch / name / 'result.json'
    return outcome(path) if path.exists() else None


def main(out, candidate):
    short = candidate.split('-')[0]
    cells = {}
    for t in TASKS:
        cells[('A', t, 2108)] = {'frozen': pass4('p4-screen-s2108', f'lcb-atcoder-{t}-A-frozen-s2108'),
                                 'cand': pass4('p4-screen-s2108', f'lcb-atcoder-{t}-A-{short}-s2108')}
        cells[('A', t, 2109)] = {'frozen': pass4('p4-stageD-agent', f'lcb-atcoder-{t}-A-frozen-s2109') or historical(t, 'A', 2109),
                                 'cand': pass4('p4-stageD-agent', f'lcb-atcoder-{t}-A-{short}-s2109')}
        for seed in (2108, 2109):
            cells[('C', t, seed)] = {'frozen': pass4('p4-stageD-agent', f'lcb-atcoder-{t}-C-frozen-s{seed}') or historical(t, 'C', seed),
                                     'cand': pass4('p4-stageD-agent', f'lcb-atcoder-{t}-C-{short}-s{seed}')}
    spot = {t: {'fresh': pass4('p4-stageD-agent', f'lcb-atcoder-{t}-C-frozen-s2108'), 'historical': historical(t, 'C', 2108)}
            for t in ('abc389_f', 'arc192_a')}

    def ok(x):
        return x is not None and x['hidden'] == 'pass'

    summary = {}
    for cond, seeds in (('A', (2109,)), ('A', (2108, 2109)), ('C', (2108, 2109))):
        keys = [k for k in cells if k[0] == cond and k[2] in seeds and cells[k]['frozen'] and cells[k]['cand']]
        gains = [f'{k[1]}/s{k[2]}' for k in keys if ok(cells[k]['cand']) and not ok(cells[k]['frozen'])]
        losses = [f'{k[1]}/s{k[2]}' for k in keys if ok(cells[k]['frozen']) and not ok(cells[k]['cand'])]
        label = f"{cond} seeds {'+'.join(map(str, seeds))}"
        summary[label] = {
            'pairs': len(keys), 'frozen_passes': sum(ok(cells[k]['frozen']) for k in keys),
            'candidate_passes': sum(ok(cells[k]['cand']) for k in keys), 'gains': gains, 'losses': losses,
            'net': len(gains) - len(losses),
            'frozen_no_program': sum(not cells[k]['frozen']['program'] for k in keys),
            'candidate_no_program': sum(not cells[k]['cand']['program'] for k in keys),
            'token_ratio': round(sum(cells[k]['cand']['output_tokens'] for k in keys) / max(1, sum(cells[k]['frozen']['output_tokens'] for k in keys)), 3),
            'wall_ratio': round(sum(cells[k]['cand']['wall_seconds'] for k in keys) / max(1e-9, sum(cells[k]['frozen']['wall_seconds'] for k in keys)), 3)}
    a9, a, c = summary['A seeds 2109'], summary['A seeds 2108+2109'], summary['C seeds 2108+2109']
    criteria = {'1_seed2109_net_ge1_losses_le1': a9['net'] >= 1 and len(a9['losses']) <= 1,
                '2_pooled_net_ge3_no_more_no_program': a['net'] >= 3 and a['candidate_no_program'] <= a['frozen_no_program'],
                '3_C_net_ge_minus1': c['net'] >= -1,
                '4_cost_le_1_5x': a['token_ratio'] <= 1.5 and a['wall_ratio'] <= 1.5}
    report = {'candidate': candidate, 'summary': summary, 'criteria': criteria, 'recommended': all(criteria.values()),
              'determinism_spot_checks': {t: {'fresh': (v['fresh'] or {}).get('submission'), 'historical': (v['historical'] or {}).get('submission'),
                                              'identical': bool(v['fresh'] and v['historical'] and v['fresh']['submission'] == v['historical']['submission'])}
                                          for t, v in spot.items()},
              'cells': {f'{k[0]}/{k[1]}/s{k[2]}': v for k, v in cells.items()}}
    Path(out).write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: {kk: vv for kk, vv in v.items()} for k, v in summary.items()}, indent=1))
    print('criteria', criteria, 'recommended', report['recommended'])
    print('spot checks', report['determinism_spot_checks'])
    for k, v in cells.items():
        f, c_ = v['frozen'] or {}, v['cand'] or {}
        print(f'{k[0]} {k[1]:9} s{k[2]}  frozen={str(f.get("hidden")):18} cand={str(c_.get("hidden")):18} ({f.get("run", "-")[:44]})')


if __name__ == '__main__':
    main(*sys.argv[1:])
