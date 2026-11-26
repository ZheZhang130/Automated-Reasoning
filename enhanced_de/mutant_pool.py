"""Reconcile and export the natural-mutant & reference pool from results/final-main.

Addresses Codex's audit requirement: produces a deterministic manifest recording
every candidate's sha256, provenance run IDs, conditions, public-pass status,
hidden verdict breakdown, and whether Condition B passed the task.
"""
import collections
import csv
import json
from pathlib import Path

from guided_agent.common import REPO, sha256_file, utc_now, write_json


def build_final_main_mutant_pool(
    results_root=REPO / 'results/final-main',
    out_manifest=None,
):
    results_root = Path(results_root)
    runs = list(csv.DictReader((results_root / 'report/runs.csv').open(encoding='utf-8')))

    by_task = collections.defaultdict(lambda: {
        'difficulty': None,
        'exposure_subgroup': None,
        'b_passes': 0,
        'b_total': 0,
        'candidates': {},  # sha256 -> info
    })

    for r in runs:
        tid = r['task_id']
        tinfo = by_task[tid]
        tinfo['difficulty'] = r['difficulty']
        tinfo['exposure_subgroup'] = r['exposure_subgroup']
        if r['condition'] == 'B':
            tinfo['b_total'] += 1
            if r['passed'] == 'True':
                tinfo['b_passes'] += 1

        sub_path = results_root / 'batch/runs' / r['run_dir'] / 'submission.py'
        if not sub_path.is_file():
            continue
        sha = sha256_file(sub_path)
        ev_path = results_root / 'batch/eval' / f"{r['run_id']}.json"
        ev = json.loads(ev_path.read_text(encoding='utf-8'))
        vc = ev.get('verdict_counts') or {}
        if ev.get('status') == 'pass':
            dom_verdict = 'AC'
        else:
            dom_verdict = max((k for k in vc if k != 'AC'), key=lambda k: vc[k], default=ev.get('status', '?'))

        cands = tinfo['candidates']
        if sha not in cands:
            cands[sha] = {
                'submission_sha256': sha,
                'rel_path': str(sub_path.relative_to(REPO)).replace('\\', '/'),
                'run_ids': [],
                'conditions': [],
                'any_public_pass': False,
                'hidden_status': ev.get('status'),
                'hidden_passed': ev.get('passed'),
                'hidden_total': ev.get('total'),
                'verdict_counts': vc,
                'dominant_verdict': dom_verdict,
            }
        rec = cands[sha]
        rec['run_ids'].append(r['run_id'])
        if r['condition'] not in rec['conditions']:
            rec['conditions'].append(r['condition'])
        if r['final_public_pass'] == 'True':
            rec['any_public_pass'] = True

    tasks_out = {}
    summary = {
        'total_tasks_in_final_main': len(by_task),
        'tasks_with_ref_and_any_mutant': 0,
        'tasks_with_ref_and_public_pass_mutant': 0,
        'tasks_with_b_ref_and_public_pass_mutant': 0,
        'distinct_references': 0,
        'distinct_all_mutants': 0,
        'distinct_public_pass_mutants': 0,
        'distinct_public_pass_mutants_b_solved': 0,
        'public_pass_mutants_by_verdict': collections.Counter(),
    }

    for tid, tinfo in sorted(by_task.items()):
        refs = []
        pub_pass_mutants = []
        pub_fail_mutants = []
        for sha, c in sorted(tinfo['candidates'].items()):
            c['conditions'].sort()
            if c['hidden_status'] == 'pass':
                refs.append(c)
            elif c['any_public_pass']:
                pub_pass_mutants.append(c)
            else:
                pub_fail_mutants.append(c)

        has_ref = len(refs) > 0
        b_solved = tinfo['b_passes'] > 0
        if has_ref and (pub_pass_mutants or pub_fail_mutants):
            summary['tasks_with_ref_and_any_mutant'] += 1
            summary['distinct_references'] += len(refs)
            summary['distinct_all_mutants'] += len(pub_pass_mutants) + len(pub_fail_mutants)
        if has_ref and pub_pass_mutants:
            summary['tasks_with_ref_and_public_pass_mutant'] += 1
            summary['distinct_public_pass_mutants'] += len(pub_pass_mutants)
            for m in pub_pass_mutants:
                summary['public_pass_mutants_by_verdict'][m['dominant_verdict']] += 1
            if b_solved:
                summary['tasks_with_b_ref_and_public_pass_mutant'] += 1
                summary['distinct_public_pass_mutants_b_solved'] += len(pub_pass_mutants)

        if has_ref and (pub_pass_mutants or pub_fail_mutants):
            tasks_out[tid] = {
                'task_id': tid,
                'difficulty': tinfo['difficulty'],
                'exposure_subgroup': tinfo['exposure_subgroup'],
                'b_passes': tinfo['b_passes'],
                'b_total': tinfo['b_total'],
                'b_solved': b_solved,
                'references': refs,
                'public_pass_mutants': pub_pass_mutants,
                'public_fail_mutants': pub_fail_mutants,
            }

    summary['public_pass_mutants_by_verdict'] = dict(summary['public_pass_mutants_by_verdict'])
    manifest = {
        'schema': 'csc2108-mutant-pool-v1',
        'created_utc': utc_now(),
        'source': 'results/final-main',
        'summary': summary,
        'tasks': tasks_out,
    }
    if out_manifest:
        write_json(out_manifest, manifest)
    return manifest
