"""B versus C (and A) economics on the 12-task pass-3 hard cohort (Phase VI).

usage: python reasoning_effectiveness/pass4/diagnostics/cost_comparison.py OUT.json

Sources (outside Git): pass-3 ext-s2108/ext-s2109 (A, C at two seeds, Codex plan-v1 artifacts), pass-4 B batches
(Codex coder on all 12 tasks; direct API coder on 2), every measured API guidance artifact of passes 1-3, and the
pass-3 direct-API B runs on two easier tasks.

Measured versus modelled is explicit:
* API dollars come only from the ledger (``cost_usd``) of direct API requests;
* a "modelled API plan cost" for the Codex-authored hard-cohort plans uses Codex's output tokens (which include its
  reasoning) at the standard output price plus the mean measured API plan input, and is labelled modelled;
* local electricity is modelled from local inference seconds with stated assumptions (default 350 W for the
  GPU-heavy system during inference and USD 0.15/kWh); GPU time itself is the measured inference seconds.
"""
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from guided_agent import measurement  # noqa: E402

D = Path('E:/CSC2108Local')
HARD = ['abc388_f', 'abc389_f', 'abc390_f', 'abc391_f', 'abc395_f', 'abc397_e', 'abc397_f', 'arc190_c', 'arc193_a',
        'arc193_b', 'arc194_e', 'arc195_d']
PRICE_IN, PRICE_OUT = 2.00, 10.00   # USD per 1M tokens, gpt-6.2-sol standard tier (rechecked 2026-11-23)
WATTS, USD_PER_KWH = 350.0, 0.15    # modelling assumptions, not measurements


def runs(batch_glob):
    out = []
    for result in sorted(D.glob(batch_glob + '/*/result.json')):
        if '.incomplete-' in result.parent.name:
            continue
        doc = measurement.build(result.parent)
        out.append(doc)
    return out


def row(doc):
    return {'task': doc['identity']['task_id'].split('-')[-1], 'seed': doc['identity']['seed'],
            'pass': doc['correctness']['hidden_status'] == 'pass', 'program': doc['correctness']['candidate_produced'],
            'local_output_tokens': doc['local_inference']['completion_tokens'] or 0,
            'local_prompt_tokens': doc['local_inference']['prompt_tokens'] or 0,
            'local_inference_seconds': doc['local_inference']['total_inference_seconds'] or 0.0,
            'wall_seconds': doc['time']['wall_seconds'], 'frontier_requests': doc['frontier']['n_requests'],
            'frontier_output_tokens': sum((r['output_tokens'] or 0) for r in doc['frontier']['requests']),
            'frontier_input_tokens': sum((r['input_tokens'] or 0) for r in doc['frontier']['requests']),
            'api_cost_usd': doc['frontier']['cost_usd'], 'actions': doc['agent']['actions']}


def summarize(rows, label, api_cost_per_attempt=None, note=''):
    n = len(rows)
    passes = sum(r['pass'] for r in rows)
    infer = sum(r['local_inference_seconds'] for r in rows)
    energy = infer * WATTS / 3.6e6
    out = {'label': label, 'attempts': n, 'hidden_passes': passes, 'pass_rate': round(passes / n, 3) if n else None,
           'no_program': sum(not r['program'] for r in rows),
           'local_inference_seconds_total': round(infer, 1),
           'local_inference_seconds_per_attempt': round(infer / n, 1) if n else None,
           'local_output_tokens_per_attempt': round(sum(r['local_output_tokens'] for r in rows) / n) if n else None,
           'wall_seconds_per_attempt': round(sum(r['wall_seconds'] or 0 for r in rows) / n, 1) if n else None,
           'frontier_requests_per_attempt': round(sum(r['frontier_requests'] for r in rows) / n, 2) if n else None,
           'modelled_local_energy_kwh_per_attempt': round(energy / n, 6) if n else None,
           'modelled_local_cost_usd_per_attempt': round(energy * USD_PER_KWH / n, 6) if n else None, 'note': note}
    if api_cost_per_attempt is not None:
        out['api_cost_usd_per_attempt'] = round(api_cost_per_attempt, 5)
        out['api_cost_usd_per_success'] = round(api_cost_per_attempt * n / passes, 5) if passes else None
    return out


def main(out):
    a = [row(d) for d in runs('reasoning-effectiveness-pass3/runs/ext-s210*') if d['identity']['condition'] == 'A']
    c_docs = [d for d in runs('reasoning-effectiveness-pass3/runs/ext-s210*') if d['identity']['condition'] == 'C']
    c = [row(d) for d in c_docs]
    b_codex = [row(d) for d in runs('reasoning-effectiveness-pass4-b/runs/p4-b-codex*')]
    b_api = [row(d) for d in runs('reasoning-effectiveness-pass4-b/runs/p4-b-api')]
    b_api_easy = [row(d) for d in runs('reasoning-effectiveness-pass3/runs/b-real*-api')]
    # measured API guidance (plans) of passes 1-3
    api_plans = []
    for path in D.glob('reasoning-effectiveness*/guidance/*/*.plan-v1.api.json'):
        raw = json.loads(path.read_text(encoding='utf-8'))
        if raw.get('schema') == 'csc2108-guidance-v1':
            api_plans.append({'task': raw['task_id'], 'cost_usd': raw['cost_usd'],
                              'input': (raw.get('usage') or {}).get('prompt_tokens'),
                              'output': (raw.get('usage') or {}).get('completion_tokens')})
    unique = {p['task']: p for p in api_plans}.values()
    mean_plan_cost = statistics.mean(p['cost_usd'] for p in unique)
    mean_plan_input = statistics.mean(p['input'] for p in unique)
    # modelled API cost of the hard-cohort Codex plans (one per task, shared by both seeds)
    plan_costs = {}
    for d in c_docs:
        request = next(r for r in d['frontier']['requests'] if r['type'] == 'guidance')
        plan_costs[d['identity']['task_id']] = (mean_plan_input * PRICE_IN + (request['output_tokens'] or 0) * PRICE_OUT) / 1e6
    modelled_plan = statistics.mean(plan_costs.values())
    b_api_cost = statistics.mean(r['api_cost_usd'] for r in b_api) if b_api else None
    b_api_easy_cost = statistics.mean(r['api_cost_usd'] for r in b_api_easy) if b_api_easy else None
    report = {
        'assumptions': {'price_per_1m': {'input': PRICE_IN, 'output': PRICE_OUT}, 'modelled_watts': WATTS,
                        'modelled_usd_per_kwh': USD_PER_KWH},
        'measured_api_plan_costs': sorted(unique, key=lambda p: p['task']),
        'mean_measured_api_plan_cost_usd': round(mean_plan_cost, 5),
        'modelled_api_plan_cost_hard_cohort_usd': round(modelled_plan, 5),
        'b_api_runs_hard': b_api, 'b_api_runs_easier_pass3': b_api_easy,
        'summary': [
            summarize(a, 'A local only (pass-3, 12 hard x 2 seeds)', 0.0),
            summarize(c, 'C one-off plan per attempt (modelled API plan cost)', modelled_plan,
                      'plan generated for this attempt only'),
            summarize(c, 'C plan amortized over 2 seeds', modelled_plan / 2, 'benchmark reuse; not a one-off cost'),
            summarize(c, 'C plan amortized over 3 seeds', modelled_plan / 3, 'benchmark reuse; not a one-off cost'),
            summarize(b_codex, 'B Codex coder (replay; no API charge; 12 hard x 1)', None,
                      'cost not measured: Codex replay; token counts include Codex harness context'),
            summarize(b_api, 'B direct API (2 hard tasks; measured)', b_api_cost),
            summarize(b_api_easy, 'B direct API (pass-3, 2 easier tasks; measured)', b_api_easy_cost),
        ],
        'per_task_hard': {t: {'A_passes': sum(r['pass'] for r in a if r['task'] == t),
                              'C_passes': sum(r['pass'] for r in c if r['task'] == t),
                              'B_codex_pass': next((r['pass'] for r in b_codex if r['task'] == t), None),
                              'B_api_pass': next((r['pass'] for r in b_api if r['task'] == t), None),
                              'B_api_cost_usd': next((r['api_cost_usd'] for r in b_api if r['task'] == t), None),
                              'C_modelled_plan_cost_usd': round(plan_costs.get('lcb-atcoder-' + t, 0), 5),
                              'C_local_inference_seconds_mean': round(statistics.mean(
                                  [r['local_inference_seconds'] for r in c if r['task'] == t] or [0]), 1)}
                          for t in HARD},
    }
    Path(out).write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8', newline='\n')
    for s in report['summary']:
        print(json.dumps(s))
    print('mean measured API plan cost', report['mean_measured_api_plan_cost_usd'], 'modelled hard plan', report['modelled_api_plan_cost_hard_cohort_usd'])


if __name__ == '__main__':
    main(*sys.argv[1:])
