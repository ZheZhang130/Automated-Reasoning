"""Summarize official paired correctness and resource costs; never emit candidate code."""
import argparse
import collections
import csv
import json
import random
import re
import statistics
from pathlib import Path

from optlib import DATA, ROOT, read, save


def quantiles(values):
    if not values:
        return None
    values = sorted(values)
    return {'min': values[0], 'p25': values[round((len(values)-1)*.25)], 'median': statistics.median(values),
            'p75': values[round((len(values)-1)*.75)], 'p90': values[round((len(values)-1)*.9)], 'max': values[-1]}


def interval(values):
    if not values:
        return None
    rng = random.Random(2108)
    samples = sorted(statistics.mean(rng.choices(values, k=len(values))) for _ in range(10000))
    return [samples[249], samples[9749]]


def collect(batch):
    plan = read(batch / 'plan.json')
    tasks = {t['task_id']: t for t in plan['manifest']['tasks']}
    rows = []
    for job in plan['jobs']:
        slot = batch / 'runs' / job['key']
        if not (slot / 'complete.json').exists():
            continue
        path = Path(read(slot / 'complete.json')['attempt'])
        r, judge = read(path / 'result.json'), read(path / 'private_evaluation.json')
        assessment = read(path/'timeout-assessment.json') if (path/'timeout-assessment.json').exists() else {}
        inf = r['inference']
        checker = re.compile(r'^\s*python(?:3)?\s+(?:-I\s+)?/public/check\.py(?:\s*<\s*[^;&|\s]+)?(?:\s+2>&1)?\s*$')
        tests = [e for e in r['events'] if e.get('recognized_public_test') or checker.fullmatch(e.get('command',''))]
        seen_failure = recovered = False
        for test in tests:
            if test['returncode']:
                seen_failure = True
            elif seen_failure:
                recovered = True
        loaded = [m for m in r.get('ollama_ps', {}).get('models', []) if m['name'] == job['model']]
        allocation = loaded[0] if loaded else {}
        samples = read(path / 'gpu-samples.json') if (path / 'gpu-samples.json').exists() else []
        memory, utilization = [], []
        for sample in samples:
            try:
                values = [float(v.strip()) for v in sample['values'].split(',')]
                memory.append(values[0]); utilization.append(values[1])
            except ValueError:
                pass
        raw = read(path / 'ollama-responses.json')
        rows.append({**job, 'batch': batch.name, 'difficulty': tasks[job['task_id']]['difficulty'], 'platform': tasks[job['task_id']]['platform'],
            'correct': int(judge['status'] == 'pass'), 'official_status': judge['status'], 'agent_status': assessment.get('effective_status',r['status']),
            'seconds': r['elapsed_seconds'], 'actions': r['actions'], 'repairs': r['repairs'], 'model_calls': r['model_calls'],
            'format_errors': r.get('format_errors', 0), 'public_tests': len(tests), 'public_failure': seen_failure, 'public_recovery': recovered,
            'recovery_official_pass': seen_failure and judge['status'] == 'pass',
            'public_pass_official_fail': any(t['returncode'] == 0 for t in tests) and judge['status'] != 'pass',
            'repeated_source_tests': sum(a['source_sha256'] == b['source_sha256'] for a,b in zip(tests,tests[1:])),
            'prompt_tokens': inf['prompt_eval_count'], 'output_tokens': inf['eval_count'],
            'generation_seconds': inf['eval_duration']/1e9, 'prefill_seconds': inf['prompt_eval_duration']/1e9, 'load_seconds': inf['load_duration']/1e9,
            'max_prompt': inf['maximum_prompt_tokens'], 'length_responses': inf['done_reasons'].count('length'),
            'context_events': len(r['context_events']), 'allocation_bytes': allocation.get('size'), 'gpu_bytes': allocation.get('size_vram'),
            'offload': bool(allocation) and allocation['size_vram'] < allocation['size'],
            'peak_gpu_mb': max(memory) if memory else None, 'median_gpu_utilization': statistics.median(utilization) if utilization else None,
            'thinking_chars': sum(len(x.get('message', {}).get('thinking', '')) for x in raw),
            'content_chars': sum(len(x.get('message', {}).get('content', '')) for x in raw),
            'wire_verified': r.get('sampler_wire_verified'), 'native_history_verified': r.get('native_history_wire_verified'),
            'telemetry_complete': r['token_telemetry_complete'], 'attempt': str(path)})
        rows[-1]['unobserved_model_calls'] = r.get('unobserved_model_calls', 0)
        rows[-1]['unobserved_output_token_upper_bound'] = r.get('unobserved_output_token_upper_bound', 0)
        starter_hash = tasks[job['task_id']].get('public_sha256', {}).get('solution.py')
        rows[-1]['unchanged_starter'] = bool(starter_hash) and r.get('submission_sha256') == starter_hash
        rows[-1]['invocation_wall_seconds'] = read(path/'invocation-timing.json')['wall_seconds'] if (path/'invocation-timing.json').exists() else None
        rows[-1]['official_error_codes'] = ','.join(str(m.get('error_code','')) for m in judge.get('metadata',[]))
        rows[-1]['raw_agent_status'] = r['status']
        rows[-1]['raw_recognized_public_tests'] = len(r['public_tests'])
        rows[-1]['posthoc_direct_checker_events'] = sum(not e.get('recognized_public_test') for e in tests)
    return plan, rows


def summarize(batch):
    plan, rows = collect(batch)
    profiles = {}
    for profile in plan['profiles']:
        selected = [r for r in rows if r['profile'] == profile]
        if not selected:
            continue
        correct = [r for r in selected if r['correct']]
        failed = [r for r in selected if not r['correct']]
        profiles[profile] = {'n': len(selected), 'passed': len(correct), 'accuracy': len(correct)/len(selected),
            'difficulty': {d: {'n': sum(r['difficulty']==d for r in selected), 'passed': sum(r['correct'] for r in selected if r['difficulty']==d)} for d in ['easy','medium','hard']},
            'seconds': quantiles([r['seconds'] for r in selected]), 'successful_seconds': quantiles([r['seconds'] for r in correct]),
            'failed_seconds': quantiles([r['seconds'] for r in failed]),
            'totals': {key: sum(r[key] for r in selected) for key in ['seconds','output_tokens','prompt_tokens','generation_seconds','prefill_seconds','load_seconds','actions','model_calls','format_errors','length_responses','context_events','public_tests','public_failure','public_recovery','recovery_official_pass','public_pass_official_fail','repeated_source_tests','thinking_chars']},
            'failed_cost': {key: sum(r[key] for r in failed) for key in ['seconds','output_tokens','generation_seconds']},
            'terminations': dict(collections.Counter(r['agent_status'] for r in selected)),
            'official_statuses': dict(collections.Counter(r['official_status'] for r in selected)),
            'unchanged_starter_runs': sum(r['unchanged_starter'] for r in selected),
            'offloaded_runs': sum(r['offload'] for r in selected), 'missing_gpu_snapshots': sum(r['gpu_bytes'] is None for r in selected),
            'maximum_prompt_tokens': max(r['max_prompt'] for r in selected),
            'unobserved_model_calls': sum(r['unobserved_model_calls'] for r in selected),
            'output_tokens_unobserved_upper_bound': sum(r['unobserved_output_token_upper_bound'] for r in selected),
            'output_tokens_distribution': quantiles([r['output_tokens'] for r in selected])}
        profiles[profile]['model_calls_distribution'] = quantiles([r['model_calls'] for r in selected])
        profiles[profile]['actions_distribution'] = quantiles([r['actions'] for r in selected])
        profiles[profile]['posthoc_direct_checker_events'] = sum(r['posthoc_direct_checker_events'] for r in selected)
        profiles[profile]['official_error_codes'] = dict(collections.Counter(r['official_error_codes'] for r in selected if not r['correct']))
        invocation_times = [r['invocation_wall_seconds'] for r in selected if r['invocation_wall_seconds'] is not None]
        profiles[profile]['invocation_wall_seconds'] = quantiles(invocation_times)
        profiles[profile]['invocation_wall_total'] = sum(invocation_times)
        by_problem = collections.defaultdict(list)
        for r in selected:
            by_problem[r['task_id']].append(r['correct'])
        profiles[profile]['problem_bootstrap_95'] = interval([statistics.mean(v) for v in by_problem.values()])
        duration = profiles[profile]['totals']['generation_seconds']
        profiles[profile]['observed_generation_tokens_per_second'] = profiles[profile]['totals']['output_tokens']/duration if duration else None
    paired = []
    names = list(profiles)
    for i, a in enumerate(names):
        for b in names[i+1:]:
            aa = {(r['task_id'],r['seed']): r for r in rows if r['profile']==a}
            bb = {(r['task_id'],r['seed']): r for r in rows if r['profile']==b}
            keys = sorted(set(aa)&set(bb))
            diffs = collections.defaultdict(list)
            for k in keys:
                diffs[k[0]].append(bb[k]['correct']-aa[k]['correct'])
            paired.append({'a': a,'b': b,'paired_runs': len(keys),'paired_problems': len(diffs),
                'b_minus_a_correct': sum(bb[k]['correct']-aa[k]['correct'] for k in keys),
                'problem_mean_accuracy_difference': statistics.mean(statistics.mean(v) for v in diffs.values()) if diffs else None,
                'problem_bootstrap_95': interval([statistics.mean(v) for v in diffs.values()]),
                'a_only_pass': sum(aa[k]['correct'] and not bb[k]['correct'] for k in keys),
                'b_only_pass': sum(bb[k]['correct'] and not aa[k]['correct'] for k in keys),
                'a_seconds': sum(aa[k]['seconds'] for k in keys), 'b_seconds': sum(bb[k]['seconds'] for k in keys),
                'a_tokens': sum(aa[k]['output_tokens'] for k in keys), 'b_tokens': sum(bb[k]['output_tokens'] for k in keys)})
    frontier = []
    coverage = {p: {(r['task_id'],r['seed']) for r in rows if r['profile']==p} for p in profiles}
    for p,x in profiles.items():
        if not any(q!=p and coverage[q]==coverage[p] and y['accuracy']>=x['accuracy'] and y['totals']['seconds']<=x['totals']['seconds'] and y['totals']['output_tokens']<=x['totals']['output_tokens'] and
                   (y['accuracy']>x['accuracy'] or y['totals']['seconds']<x['totals']['seconds'] or y['totals']['output_tokens']<x['totals']['output_tokens']) for q,y in profiles.items()):
            frontier.append(p)
    summary = {'batch': str(batch), 'planned': len(plan['jobs']), 'completed': len(rows), 'profiles': profiles, 'paired': paired,
               'descriptive_three_metric_frontier': frontier, 'frontier_warning': 'Compare only identical complete task/seed coverage; incomplete arms are not comparable.'}
    save(batch / 'analysis.json', summary)
    if rows:
        with (batch / 'metrics.csv').open('w', newline='', encoding='utf-8') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    return summary


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('batch',type=Path)
    p.add_argument('--export',type=Path)
    args=p.parse_args()
    summary=summarize(args.batch)
    if args.export:
        save(args.export,summary)
    compact = {p: {'passed':x['passed'], 'n':x['n'], 'seconds':round(x['totals']['seconds'],1),
                   'tokens':x['totals']['output_tokens'], 'formats':x['totals']['format_errors']}
               for p,x in summary['profiles'].items()}
    print(json.dumps({'completed':summary['completed'], 'planned':summary['planned'], 'profiles':compact}),flush=True)
