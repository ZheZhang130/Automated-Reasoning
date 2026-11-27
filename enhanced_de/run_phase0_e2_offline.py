"""Phase 0 offline benchmark for E2-Review and E2-Strict (CPU/Docker only, zero GPU).

Evaluates:
1. E2-Review on all 16 Phase 1A historical A final submissions (10 public_pass_hidden_fail
   + 6 hidden-passing safety non-regression submissions): measures DEFECT rate,
   sandbox-verified delivery rate, silent-unless-verified abstention on passing code,
   and counterexample ground-truth soundness against passing references.
2. E2-Strict on all 12 Phase 1B historical E-v1 trigger states: measures schema validity,
   committed repair-mode distribution (LOCAL-FIX vs METHOD-CHANGE), V-check alignment on
   triggering candidates, reference soundness, and retroactive catch rate on the 7
   historical E-v1 post-diagnosis public_pass_hidden_fail submissions.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import re
from types import SimpleNamespace

from guided_agent.common import REPO, read_json, sha256_bytes, utc_now, write_json

from . import e2_diagnosis
from .runner_v2 import load_public_cases, load_statement


DEFAULT_STUDY = Path(r'E:\CSC2108Local\enhanced-de-v2-study')
FINAL_STUDY_RUNS = Path(r'E:\CSC2108Local\final-study\runs\final-main')
FINAL_MAIN_BATCH = REPO / 'results' / 'final-main' / 'batch' / 'runs'
DEV_COHORTS = REPO / 'enhanced_de' / 'manifests' / 'dev_cohorts.json'
MUTANT_POOL = REPO / 'enhanced_de' / 'manifests' / 'mutant_pool_final_main.json'


def _extract_block(user_msg, nonce, name):
    m = re.search(
        rf'<<<DATA-{re.escape(nonce)} {re.escape(name)}>>>\n(.*?)\n<<<END-DATA-{re.escape(nonce)}>>>',
        user_msg,
        re.DOTALL,
    )
    if not m:
        raise ValueError(f'Block {name!r} with nonce {nonce!r} not found')
    return m.group(1)


def _dummy_budget(actions=2, limit=20, repairs=0, repair_limit=3):
    return SimpleNamespace(actions=actions, action_limit=limit, repairs=repairs, repair_limit=repair_limit)


def _ref_paths_for_task(pool_tasks, task_id, max_refs=2):
    entry = pool_tasks.get(task_id) or {}
    paths = [REPO / r['rel_path'] for r in entry.get('references', [])[:max_refs]]
    if not paths:
        # Fallback: find any passing B submission in results/final-main/batch/runs
        for s in (2108, 2109, 2110):
            p = FINAL_MAIN_BATCH / f'{task_id}-B-s{s}' / 'submission.py'
            if p.is_file():
                paths.append(p)
                if len(paths) >= max_refs:
                    break
    return paths


def eval_review_one(pair, *, is_pphf, study, provider_name, pool_tasks):
    tid, seed = pair['task_id'], int(pair['seed'])
    key = f'{tid}-A-s{seed}'
    out_dir = Path(study) / 'e2_offline' / 'review' / provider_name
    out_dir.mkdir(parents=True, exist_ok=True)
    rec_path = out_dir / f'{key}.review.json'
    if rec_path.exists():
        return read_json(rec_path)

    sub_path = FINAL_MAIN_BATCH / f'{tid}-A-s{seed}' / 'submission.py'
    source = sub_path.read_bytes()
    stmt = load_statement(study, tid)
    pub_cases = load_public_cases(study, tid)
    pub_res = {
        'suite': 'public',
        'status': 'pass',
        'passed': len(pub_cases),
        'total': len(pub_cases),
        'report': f'PUBLIC TESTS: {len(pub_cases)}/{len(pub_cases)} passed\n',
        'code_sha256': sha256_bytes(source),
        'time_limit_s': 2.0,
    }
    packet = e2_diagnosis.program_packet(
        kind='review',
        prompt_id='E2_REVIEW_V1',
        statement=stmt,
        source=source,
        result=pub_res,
        task_id=tid,
        budget=_dummy_budget(actions=2),
        seconds_left=540.0,
    )
    prov = e2_diagnosis.make_e2_provider({'provider': provider_name, 'model': 'gpt-6.2-sol', 'effort': 'medium'}, study)
    ev_dir = out_dir / f'{key}.provider'
    if ev_dir.exists():
        import shutil
        shutil.rmtree(ev_dir)
    resp = prov(e2_diagnosis.E2_REVIEW_V1, packet['user_message'], ev_dir, packet=packet)
    text = resp['text']
    problems, parsed = e2_diagnosis.validate_review(text)
    verdict = parsed.get('verdict')
    checks = e2_diagnosis.filter_against_public(parsed.get('checks') or [], pub_cases) if verdict == 'DEFECT' else []
    ref_paths = _ref_paths_for_task(pool_tasks, tid, max_refs=2)

    evaluated_checks = []
    verified_count = 0
    verified_ref_sound = 0
    verified_ref_false = 0
    for chk in checks:
        c_rec = {'id': chk['id'], 'dropped': chk['dropped'], 'malformed': chk.get('malformed')}
        if not chk['dropped']:
            run = e2_diagnosis.docker_sandbox_runner(source, chk['stdin'], 2.0)
            cand_out = e2_diagnosis.classify_run(run, chk['expected'])
            c_rec['candidate_outcome'] = cand_out
            is_ver = cand_out in ('WA', 'RE', 'TLE')
            c_rec['verified'] = is_ver
            if is_ver:
                verified_count += 1
                ref_outcomes = []
                for rp in ref_paths:
                    rr = e2_diagnosis.docker_sandbox_runner(rp.read_bytes(), chk['stdin'], 2.0)
                    ref_outcomes.append(e2_diagnosis.classify_run(rr, chk['expected']))
                c_rec['ref_outcomes'] = ref_outcomes
                if ref_outcomes and all(o == 'AC' for o in ref_outcomes):
                    verified_ref_sound += 1
                elif ref_outcomes:
                    verified_ref_false += 1
        evaluated_checks.append(c_rec)

    if problems:
        outcome = 'validation_error'
    elif verdict == 'NO-DEFECT':
        outcome = 'no_defect'
    elif verified_count > 0:
        outcome = 'verified_delivered'
    else:
        outcome = 'unverified_abstain'

    rec = {
        'task_id': tid,
        'seed': seed,
        'group': 'pphf' if is_pphf else 'safety_pass',
        'provider': provider_name,
        'a_verdict': pair.get('a_verdict', 'AC'),
        'validation_problems': problems,
        'verdict': verdict,
        'review_outcome': outcome,
        'checks': evaluated_checks,
        'verified_count': verified_count,
        'verified_ref_sound': verified_ref_sound,
        'verified_ref_false': verified_ref_false,
        'wall_seconds': resp.get('harness_wall_seconds'),
        'created_utc': utc_now(),
    }
    write_json(rec_path, rec)
    return rec


def eval_strict_one(pair, *, study, provider_name, pool_tasks):
    tid, seed = pair['task_id'], int(pair['seed'])
    key = f'{tid}-E-s{seed}'
    out_dir = Path(study) / 'e2_offline' / 'strict' / provider_name
    out_dir.mkdir(parents=True, exist_ok=True)
    rec_path = out_dir / f'{key}.strict.json'
    if rec_path.exists():
        return read_json(rec_path)

    old_run = FINAL_STUDY_RUNS / f'{tid}-E-s{seed}'
    old_pkt = read_json(old_run / 'diagnosis' / 'packet.json')
    nonce = old_pkt['nonce']
    prog_str = _extract_block(old_pkt['user_message'], nonce, 'program')
    report_str = _extract_block(old_pkt['user_message'], nonce, 'report')
    source = prog_str.encode('utf-8')
    stmt = load_statement(study, tid)
    pub_cases = load_public_cases(study, tid)
    pub_res = {
        'suite': 'public',
        'status': 'candidate_failure',
        'passed': old_pkt.get('public_passed', 0),
        'total': old_pkt.get('public_total', len(pub_cases)),
        'first_failure': {'name': old_pkt.get('first_case'), 'verdict': old_pkt.get('verdict')},
        'report': report_str,
        'code_sha256': sha256_bytes(source),
        'time_limit_s': 2.0,
    }
    packet = e2_diagnosis.program_packet(
        kind='strict',
        prompt_id='E2_STRICT_V1',
        statement=stmt,
        source=source,
        result=pub_res,
        task_id=tid,
        budget=_dummy_budget(actions=2),
        seconds_left=540.0,
    )
    prov = e2_diagnosis.make_e2_provider({'provider': provider_name, 'model': 'gpt-6.2-sol', 'effort': 'medium'}, study)
    ev_dir = out_dir / f'{key}.provider'
    if ev_dir.exists():
        import shutil
        shutil.rmtree(ev_dir)
    resp = prov(e2_diagnosis.E2_STRICT_V1, packet['user_message'], ev_dir, packet=packet)
    text = resp['text']
    problems, parsed = e2_diagnosis.validate_strict(text)
    checks = e2_diagnosis.filter_against_public(parsed.get('checks') or [], pub_cases)
    ref_paths = _ref_paths_for_task(pool_tasks, tid, max_refs=2)
    hist_final = FINAL_MAIN_BATCH / f'{tid}-E-s{seed}' / 'submission.py'
    hist_final_bytes = hist_final.read_bytes() if hist_final.is_file() else None

    vchecks = []
    aligned = 0
    aligned_ref_sound = 0
    aligned_ref_false = 0
    caught_hist_e1_final = False
    for chk in checks:
        c_rec = {'id': chk['id'], 'dropped': chk['dropped'], 'malformed': chk.get('malformed')}
        if not chk['dropped']:
            run = e2_diagnosis.docker_sandbox_runner(source, chk['stdin'], 2.0)
            trig_out = e2_diagnosis.classify_run(run, chk['expected'])
            c_rec['trigger_outcome'] = trig_out
            is_al = trig_out in ('WA', 'RE', 'TLE')
            c_rec['aligned'] = is_al
            if is_al:
                aligned += 1
                ref_outs = []
                for rp in ref_paths:
                    rr = e2_diagnosis.docker_sandbox_runner(rp.read_bytes(), chk['stdin'], 2.0)
                    ref_outs.append(e2_diagnosis.classify_run(rr, chk['expected']))
                c_rec['ref_outcomes'] = ref_outs
                if ref_outs and all(o == 'AC' for o in ref_outs):
                    aligned_ref_sound += 1
                elif ref_outs:
                    aligned_ref_false += 1
                if hist_final_bytes is not None:
                    hr = e2_diagnosis.docker_sandbox_runner(hist_final_bytes, chk['stdin'], 2.0)
                    hout = e2_diagnosis.classify_run(hr, chk['expected'])
                    c_rec['hist_e1_final_outcome'] = hout
                    if hout in ('WA', 'RE', 'TLE'):
                        caught_hist_e1_final = True
        vchecks.append(c_rec)

    rec = {
        'task_id': tid,
        'seed': seed,
        'e1_category': pair.get('e1_category'),
        'provider': provider_name,
        'validation_problems': problems,
        'repair_mode': parsed.get('repair_mode'),
        'hedge_terms': parsed.get('hedge_terms'),
        'static_risk_flags': packet.get('static_risk_flags'),
        'vchecks': vchecks,
        'aligned_count': aligned,
        'aligned_ref_sound': aligned_ref_sound,
        'aligned_ref_false': aligned_ref_false,
        'caught_hist_e1_final': caught_hist_e1_final,
        'wall_seconds': resp.get('harness_wall_seconds'),
        'created_utc': utc_now(),
    }
    write_json(rec_path, rec)
    return rec


def main():
    p = argparse.ArgumentParser(description='Offline E2-Review and E2-Strict Phase 0 benchmark')
    p.add_argument('--study', default=str(DEFAULT_STUDY))
    p.add_argument('--provider', default='codex', choices=['codex'])
    p.add_argument('--workers', type=int, default=2)
    args = p.parse_args()

    study = Path(args.study)
    cohorts = read_json(DEV_COHORTS)
    pool_tasks = read_json(MUTANT_POOL)['tasks']

    safety_true_passes = [
        {'task_id': 'lcb-atcoder-abc389_d', 'seed': 2108},
        {'task_id': 'lcb-atcoder-abc398_b', 'seed': 2108},
        {'task_id': 'lcb-atcoder-abc393_f', 'seed': 2108},
        {'task_id': 'lcb-atcoder-abc393_f', 'seed': 2109},
        {'task_id': 'lcb-atcoder-abc395_e', 'seed': 2108},
        {'task_id': 'lcb-atcoder-abc395_e', 'seed': 2109},
    ]
    review_jobs = (
        [(x, True) for x in cohorts['phase1a_d2_and_review_pphf_pairs']]
        + [(x, False) for x in safety_true_passes]
    )
    strict_jobs = cohorts['phase1b_e2_strict_triggered_failure_pairs']

    print(f'=== Phase 0 Offline E2-Review ({len(review_jobs)} states) & E2-Strict ({len(strict_jobs)} states) ===', flush=True)
    review_recs = []
    strict_recs = []

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        rfuts = {ex.submit(eval_review_one, pair, is_pphf=is_pphf, study=study, provider_name=args.provider, pool_tasks=pool_tasks): pair for pair, is_pphf in review_jobs}
        sfuts = {ex.submit(eval_strict_one, pair, study=study, provider_name=args.provider, pool_tasks=pool_tasks): pair for pair in strict_jobs}
        for fut in as_completed(rfuts):
            r = fut.result()
            review_recs.append(r)
            print(
                f"  [REVIEW {r['group']:11s}] {r['task_id'].replace('lcb-atcoder-',''):10s} s{r['seed']} | "
                f"verdict={str(r['verdict']):9s} outcome={r['review_outcome']:18s} "
                f"ver={r['verified_count']} ref_sound={r['verified_ref_sound']} ref_false={r['verified_ref_false']} "
                f"prob={r['validation_problems']}",
                flush=True,
            )
        for fut in as_completed(sfuts):
            s = fut.result()
            strict_recs.append(s)
            print(
                f"  [STRICT {str(s['e1_category'])[:16]:16s}] {s['task_id'].replace('lcb-atcoder-',''):10s} s{s['seed']} | "
                f"mode={str(s['repair_mode']):13s} aligned={s['aligned_count']} "
                f"ref_sound={s['aligned_ref_sound']} ref_false={s['aligned_ref_false']} "
                f"caught_e1={s['caught_hist_e1_final']} prob={s['validation_problems']}",
                flush=True,
            )

    pphf = [r for r in review_recs if r['group'] == 'pphf']
    safe = [r for r in review_recs if r['group'] == 'safety_pass']
    strict_pphf = [s for s in strict_recs if str(s['e1_category']).startswith('public_pass_hidden_fail')]

    report = {
        'schema': 'csc2108-phase0-e2-offline-report-v1',
        'provider': args.provider,
        'created_utc': utc_now(),
        'review_summary': {
            'pphf_total': len(pphf),
            'pphf_verdict_defect': sum(r['verdict'] == 'DEFECT' for r in pphf),
            'pphf_verified_delivered': sum(r['review_outcome'] == 'verified_delivered' for r in pphf),
            'pphf_verified_ref_sound': sum(r['verified_ref_sound'] for r in pphf),
            'pphf_verified_ref_false': sum(r['verified_ref_false'] for r in pphf),
            'safety_total': len(safe),
            'safety_no_defect': sum(r['review_outcome'] == 'no_defect' for r in safe),
            'safety_unverified_abstain': sum(r['review_outcome'] == 'unverified_abstain' for r in safe),
            'safety_false_delivered': sum(r['review_outcome'] == 'verified_delivered' for r in safe),
            'safety_validation_errors': sum(bool(r['validation_problems']) for r in safe),
        },
        'strict_summary': {
            'total': len(strict_recs),
            'valid_schema': sum(not s['validation_problems'] for s in strict_recs),
            'local_fix': sum(s['repair_mode'] == 'LOCAL-FIX' for s in strict_recs),
            'method_change': sum(s['repair_mode'] == 'METHOD-CHANGE' for s in strict_recs),
            'with_aligned_vcheck': sum(s['aligned_count'] > 0 for s in strict_recs),
            'total_aligned_vchecks': sum(s['aligned_count'] for s in strict_recs),
            'aligned_ref_sound': sum(s['aligned_ref_sound'] for s in strict_recs),
            'aligned_ref_false': sum(s['aligned_ref_false'] for s in strict_recs),
            'hist_e1_pphf_total': len(strict_pphf),
            'hist_e1_pphf_caught_by_vchecks': sum(bool(s['caught_hist_e1_final']) for s in strict_pphf),
        },
        'review_records': sorted(review_recs, key=lambda x: (x['group'], x['task_id'], x['seed'])),
        'strict_records': sorted(strict_recs, key=lambda x: (x['task_id'], x['seed'])),
    }
    out_path = study / 'reports' / f'phase0_e2_offline_{args.provider}.json'
    write_json(out_path, report)
    print('\n=== Phase 0 Offline E2 Summary ===', flush=True)
    print('REVIEW:', json.dumps(report['review_summary'], indent=2), flush=True)
    print('STRICT:', json.dumps(report['strict_summary'], indent=2), flush=True)


if __name__ == '__main__':
    main()
