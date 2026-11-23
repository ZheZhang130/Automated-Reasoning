"""Apply the pre-registered screening rule (PREREGISTRATION.md) to batch_table output.

usage: python reasoning_effectiveness/pass4/diagnostics/screen_analysis.py TABLE.json OUT.json [REFERENCE_AGENT]

Per agent configuration: totals and paired task-level differences against the reference (default frozen-v6),
then the four selection criteria. Rows are paired by (task, condition, seed).
"""
import json
import sys
from pathlib import Path

MEASURES = ('hidden_pass', 'program', 'first_response_truncated', 'truncated_responses', 'exact_repeats',
            'rewrites_of_failed_candidate', 'actions', 'repairs', 'format_errors', 'public_tests', 'public_pass',
            'local_output_tokens_total', 'prompt_tokens', 'eval_seconds', 'self_plan_eval_seconds', 'wall_seconds')


def value(row, key):
    if key == 'hidden_pass':
        return int(row.get('hidden') == 'pass')
    v = row.get(key)
    if isinstance(v, bool):
        return int(v)
    return v or 0


def main(table, out, reference='frozen-v6'):
    rows = json.loads(Path(table).read_text(encoding='utf-8'))
    agents = sorted({r['agent'] for r in rows})
    index = {(r['agent'], r['task'], r['condition'], r['seed']): r for r in rows}
    ref_keys = {(t, c, s) for a, t, c, s in index if a == reference}
    report = {'reference': reference, 'agents': {}}
    for agent in agents:
        keys = sorted(k for k in ref_keys if (agent, *k) in index)
        mine = [index[(agent, *k)] for k in keys]
        ref = [index[(reference, *k)] for k in keys]
        totals = {m: round(sum(value(r, m) for r in mine), 2) for m in MEASURES}
        ref_totals = {m: round(sum(value(r, m) for r in ref), 2) for m in MEASURES}
        gains = [k[0] for k, a, b in zip(keys, mine, ref) if value(a, 'hidden_pass') > value(b, 'hidden_pass')]
        losses = [k[0] for k, a, b in zip(keys, mine, ref) if value(a, 'hidden_pass') < value(b, 'hidden_pass')]
        tok_ratio = totals['local_output_tokens_total'] / max(1, ref_totals['local_output_tokens_total'])
        wall_ratio = totals['wall_seconds'] / max(1e-9, ref_totals['wall_seconds'])
        easy = next((a for k, a in zip(keys, mine) if k[0] == 'abc400_b'), None)
        criteria = {
            '1_net_plus2_max1_loss': len(gains) - len(losses) >= 2 and len(losses) <= 1,
            '2_no_more_no_program': (len(mine) - totals['program']) <= (len(ref) - ref_totals['program']),
            '3_keeps_abc400_b': easy is not None and value(easy, 'hidden_pass') == 1,
            '4_cost_within_2x': tok_ratio <= 2.0 and wall_ratio <= 2.0,
        }
        report['agents'][agent] = {
            'paired_attempts': len(keys), 'totals': totals, 'reference_totals': ref_totals,
            'gains': gains, 'losses': losses, 'net': len(gains) - len(losses),
            'output_token_ratio': round(tok_ratio, 3), 'wall_ratio': round(wall_ratio, 3),
            'criteria': criteria, 'qualifies': agent != reference and all(criteria.values()),
            'per_task': {k[0] + f'/s{k[2]}': {'hidden': a.get('hidden'), 'hidden_passed': a.get('hidden_passed'),
                                              'reference_hidden': b.get('hidden'), 'program': a.get('program'),
                                              'exit': a.get('exit'), 'reference_exit': b.get('exit')}
                         for k, a, b in zip(keys, mine, ref)},
        }
    Path(out).write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(f"{'agent':16} pass  net  gains/losses       noprog  trunc1  trunc  rep  rwf  out_tok    eval_s   wall_s  qualifies")
    for agent, a in report['agents'].items():
        t = a['totals']
        print(f"{agent:16} {t['hidden_pass']:>4} {a['net']:>+4}  {','.join(a['gains']) or '-'}/{','.join(a['losses']) or '-'}"
              f"  {a['paired_attempts'] - t['program']:>6} {t['first_response_truncated']:>6} {t['truncated_responses']:>6}"
              f" {t['exact_repeats']:>4} {t['rewrites_of_failed_candidate']:>4} {t['local_output_tokens_total']:>8}"
              f" {t['eval_seconds'] + t['self_plan_eval_seconds']:>9.1f} {t['wall_seconds']:>8.1f}  {a['qualifies']} {a['criteria']}")


if __name__ == '__main__':
    main(*sys.argv[1:])
