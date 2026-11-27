"""Process measurements for every enhanced_de live batch (development, validation, API) in one table.

For each run: trigger / delivery, whether a program was produced, local length stops (before and after delivery),
local completion tokens, frontier tokens (provider-reported; Codex counts include its harness context and are not
API-comparable), wall time, hidden outcome, and the official A outcome at the same (task, seed) where one exists.
Rows are grouped by (batch, arm).  Providers are never pooled: the batch name carries the provider.

    python -m enhanced_de.analyze_v2 [--study ...] [--out reports/process_v2.json]
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

from guided_agent.common import REPO, read_json, utc_now, write_json

STUDY = Path(r'E:\CSC2108Local\enhanced-de-v2-study')
FINAL_MAIN_RUNS = REPO / 'results' / 'final-main' / 'batch' / 'runs'
FINAL_MAIN_EVAL = REPO / 'results' / 'final-main' / 'batch' / 'eval'


def official_index():
    idx = {}
    for d in FINAL_MAIN_RUNS.iterdir():
        res = d / 'result.json'
        if not res.exists():
            continue
        rec = read_json(res)
        ev = FINAL_MAIN_EVAL / f"{rec['run_id']}.json"
        hidden = read_json(ev) if ev.exists() else {}
        idx[(rec['task_id'], rec['condition'], rec.get('seed'))] = {
            'pass': hidden.get('status') == 'pass', 'passed': hidden.get('passed'),
            'submission_sha256': rec.get('submission_sha256'), 'exit_status': rec.get('exit_status')}
    return idx


def delivery_index(rec):
    """Local-call index after which the intervention was delivered (None if never)."""
    e2 = rec.get('e2_diagnosis') or {}
    for key in ('delivered_after_model_call', 'model_calls_at_delivery', 'trigger_model_call'):
        if isinstance(e2.get(key), int):
            return e2[key]
    return None


def run_row(run_dir, rec, ev, official):
    coding = (rec.get('usage') or {}).get('coding') or []
    reasons = [c.get('done_reason') for c in coding]
    g = rec.get('guidance') or {}
    e2 = rec.get('e2_diagnosis') or {}
    d2 = rec.get('d2_gate') or {}
    guid = (rec.get('usage') or {}).get('guidance') or []
    ftok_in = ftok_out = 0
    for u in guid:
        usage = (u or {}).get('usage') or {}
        rep = usage.get('codex_reported') or usage
        ftok_in += int(rep.get('input_tokens') or rep.get('prompt_tokens') or 0)
        ftok_out += int(rep.get('output_tokens') or rep.get('completion_tokens') or 0)
    off = official.get((rec['task_id'], 'A', rec.get('seed')))
    attempts = []
    ap = Path(run_dir) / 'attempts.jsonl'
    if ap.exists():
        attempts = [json.loads(x) for x in ap.read_text(encoding='utf-8').splitlines() if x.strip()]
    statuses = [((a.get('result') or {}).get('status')) for a in attempts]
    return {
        'run_id': rec['run_id'], 'task_id': rec['task_id'], 'seed': rec.get('seed'),
        'arm': rec.get('arm') or rec.get('condition'), 'condition': rec.get('condition'),
        'exit_status': rec.get('exit_status'), 'n_actions': rec.get('n_actions'),
        'triggered': bool(g.get('triggered')), 'delivered': bool(g.get('delivered')),
        'guidance_error': g.get('error'), 'trigger_kind': e2.get('trigger_kind'),
        'repair_mode': e2.get('repair_mode_declared') or e2.get('repair_mode'),
        'review_outcome': e2.get('review_outcome'), 'd2_checks': d2.get('checks'), 'd2_failed': d2.get('failed'),
        'program': rec.get('submission_sha256') is not None,
        'length_stops': reasons.count('length'), 'local_calls': len(reasons),
        'local_completion_tokens': sum(int(c.get('completion_tokens') or 0) for c in coding),
        'frontier_input_tokens': ftok_in, 'frontier_output_tokens': ftok_out,
        'frontier_wait_seconds': rec.get('frontier_wait_seconds'),
        'wall_seconds': rec.get('wall_seconds'),
        'public_tests': len(statuses), 'public_passes': statuses.count('pass'),
        'hidden_status': (ev or {}).get('status'), 'hidden_passed': (ev or {}).get('passed'),
        'hidden_total': (ev or {}).get('total'), 'pass': (ev or {}).get('status') == 'pass' if ev else None,
        'official_A_pass': None if off is None else off['pass'],
        'same_submission_as_official_A': None if off is None else off['submission_sha256'] == rec.get('submission_sha256'),
    }


def collect(study):
    official = official_index()
    rows = []
    for bdir in sorted((Path(study) / 'runs').iterdir()):
        if not bdir.is_dir():
            continue
        for res in sorted(bdir.glob('*/result.json')):
            if '.incomplete-' in res.parent.name or '_archive' in str(res):
                continue
            rec = read_json(res)
            ev_path = bdir / 'eval' / f"{rec['run_id']}.json"
            ev = read_json(ev_path) if ev_path.exists() else None
            row = run_row(res.parent, rec, ev, official)
            row['batch'] = bdir.name
            rows.append(row)
    return rows


def aggregate(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[(r['batch'], r['arm'])].append(r)
    out = []
    for (batch, arm), rs in sorted(groups.items()):
        scored = [r for r in rs if r['pass'] is not None]
        with_a = [r for r in scored if r['official_A_pass'] is not None]
        out.append({
            'batch': batch, 'arm': arm, 'runs': len(rs), 'scored': len(scored),
            'hidden_pass': sum(r['pass'] for r in scored),
            'triggered': sum(r['triggered'] for r in rs), 'delivered': sum(r['delivered'] for r in rs),
            'program': sum(r['program'] for r in rs),
            'runs_with_length_stop': sum(r['length_stops'] > 0 for r in rs),
            'length_stops_total': sum(r['length_stops'] for r in rs),
            'local_completion_tokens_median': sorted(r['local_completion_tokens'] for r in rs)[len(rs) // 2],
            'frontier_output_tokens_total': sum(r['frontier_output_tokens'] for r in rs),
            'wall_seconds_median': sorted((r['wall_seconds'] or 0) for r in rs)[len(rs) // 2],
            'official_A_pass_same_states': sum(bool(r['official_A_pass']) for r in with_a),
            'wins_vs_official_A': sum(1 for r in with_a if r['pass'] and not r['official_A_pass']),
            'losses_vs_official_A': sum(1 for r in with_a if not r['pass'] and r['official_A_pass']),
            'hidden_cases_passed_total': sum(int(r['hidden_passed'] or 0) for r in scored),
        })
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--study', default=str(STUDY))
    p.add_argument('--out', default=None)
    args = p.parse_args()
    rows = collect(args.study)
    agg = aggregate(rows)
    out = Path(args.out) if args.out else Path(args.study) / 'reports' / 'process_v2.json'
    write_json(out, {'schema': 'csc2108-enhanced-de-process-v2', 'created_utc': utc_now(),
                     'note': 'Codex frontier token counts include harness context; not API-comparable. '
                             'official_A_* columns use the official final-main A run at the same (task, seed); '
                             'test5 tasks have no official A.',
                     'groups': agg, 'runs': rows})
    hdr = ('batch', 'arm', 'runs', 'scored', 'hidden_pass', 'triggered', 'delivered', 'program',
           'runs_with_length_stop', 'official_A_pass_same_states', 'wins_vs_official_A', 'losses_vs_official_A',
           'wall_seconds_median')
    print(' | '.join(hdr))
    for g in agg:
        print(' | '.join(str(g[h]) for h in hdr))
    print(out)


if __name__ == '__main__':
    main()
