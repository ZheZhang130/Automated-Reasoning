"""Descriptive correctness/reliability analysis with problem-paired uncertainty."""
import argparse
import collections
import csv
import itertools
import json
import math
import random
import statistics
from pathlib import Path

from common import read, save


def interval(values, seed=2108):
    if not values:
        return None
    generator = random.Random(seed)
    samples = sorted(sum(generator.choices(values, k=len(values))) / len(values) for _ in range(10000))
    return [samples[249], samples[9749]]


def analyze(batch, report_path):
    plan = read(batch / 'plan.json')
    tasks = {t['task_id']: t for t in plan['manifest']['tasks']}
    rows = []
    outcomes = collections.defaultdict(dict)
    for job in plan['jobs']:
        done = batch / 'runs' / job['key'] / 'complete.json'
        if not done.exists():
            continue
        completion = read(done)
        attempt = Path(completion['attempt'])
        result = read(attempt / 'result.json')
        judge = read(attempt / 'private_evaluation.json')
        inference = result.get('inference', {})
        tests = result.get('public_tests', [])
        public_failure_types = collections.Counter()
        for event in tests:
            if not event.get('returncode'):
                continue
            feedback = None
            for line in event.get('output', '').splitlines():
                if line.startswith('CSC2108_PUBLIC_RESULT='):
                    try:
                        feedback = json.loads(line.split('=', 1)[1])
                    except ValueError:
                        pass
            category = ('timeout' if feedback and feedback.get('status') == 'candidate_timeout' else
                        'wrong_answer' if feedback and feedback.get('returncode') == 0 else
                        'runtime_error' if feedback and feedback.get('returncode') else 'unclassified')
            public_failure_types[category] += 1
        had_failure = any(t.get('returncode') for t in tests)
        seen_failure = recovered = False
        for test in tests:
            if test.get('returncode'):
                seen_failure = True
            elif seen_failure:
                recovered = True
        loaded = [m for m in result.get('ollama_ps', {}).get('models', []) if m['name'] == job['model']]
        allocation = loaded[0] if loaded else {}
        row = {**job, 'difficulty': tasks[job['task_id']].get('difficulty', 'development'),
               'platform': tasks[job['task_id']].get('platform', 'synthetic'),
               'agent_status': result['status'], 'official_status': judge['status'], 'correct': int(judge['status'] == 'pass'),
               'seconds': result['elapsed_seconds'], 'actions': result['actions'], 'repairs': result['repairs'],
               'format_errors': result.get('format_errors', 0), 'public_tests': len(tests),
               'public_failures': sum(bool(t.get('returncode')) for t in tests),
               **{'public_' + label + '_events': public_failure_types[label] for label in ('timeout', 'wrong_answer', 'runtime_error', 'unclassified')},
               'command_failures': sum(bool(e.get('returncode')) for e in result.get('events', []) if not e.get('recognized_public_test')),
               'public_recovery': recovered, 'recovery_to_official_pass': had_failure and judge['status'] == 'pass',
               'prompt_tokens': inference.get('prompt_eval_count'), 'output_tokens': inference.get('eval_count'),
               'generation_ns': inference.get('eval_duration'), 'prefill_ns': inference.get('prompt_eval_duration'),
               'load_ns': inference.get('load_duration'), 'context_events': len(result.get('context_events', [])),
               'model_calls': result.get('model_calls'), 'captured_calls': inference.get('calls_captured'),
               'token_telemetry_complete': result.get('token_telemetry_complete', False),
               'sampler_wire_verified': result.get('sampler_wire_verified', False),
               'maximum_prompt_tokens': inference.get('maximum_prompt_tokens'),
               'length_limited_responses': inference.get('done_reasons', []).count('length'),
               'model_allocation': allocation.get('size'), 'gpu_allocation': allocation.get('size_vram'),
               'residency_snapshot_available': bool(allocation),
               'cpu_offload': bool(allocation) and allocation['size_vram'] < allocation['size'],
               'official_error_codes': ','.join(str(m.get('error_code', '')) for m in judge.get('metadata', [])),
               'submission_sha256': result.get('submission_sha256'), 'attempt': str(attempt)}
        starter_hash = tasks[job['task_id']].get('public_sha256', {}).get('solution.py')
        row['unchanged_starter_candidate'] = bool(starter_hash) and starter_hash == result.get('submission_sha256')
        row['public_pass_official_failure'] = any(t.get('returncode') == 0 for t in tests) and judge['status'] != 'pass'
        rows.append(row)
        outcomes[job['task_id']][(job['model'], job['repetition'])] = row
    if rows:
        with (batch / 'metrics.csv').open('w', newline='', encoding='utf-8') as target:
            writer = csv.DictWriter(target, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    summary = {'planned': len(plan['jobs']), 'completed': len(rows), 'remaining': len(plan['jobs']) - len(rows),
               'profile': plan['profile'], 'profile_config': plan['profile_config'],
               'dataset_revision': plan['manifest'].get('revision'), 'models': {}, 'paired': []}
    model_problem_accuracy = {}
    for model in plan['models']:
        selected = [r for r in rows if r['model'] == model]
        per_problem = []
        duplicates = compared = 0
        for task in tasks:
            attempts = [outcomes[task].get((model, repetition)) for repetition in range(1, plan['repetitions'] + 1)]
            if all(attempts):
                per_problem.append(sum(a['correct'] for a in attempts) / len(attempts))
                hashes = [a['submission_sha256'] for a in attempts]
                if all(hashes) and len(hashes) > 1:
                    compared += 1
                    duplicates += len(set(hashes)) == 1
        model_problem_accuracy[model] = per_problem
        n = len(selected)
        passed = sum(r['correct'] for r in selected)
        generated = sum(r['output_tokens'] or 0 for r in selected)
        ns = sum(r['generation_ns'] or 0 for r in selected)
        info = {'completed': n, 'planned': len(tasks) * plan['repetitions'], 'passed': passed,
                'accuracy_completed': passed / n if n else None, 'problem_bootstrap_95': interval(per_problem),
                'complete_problem_count': len(per_problem),
                'problems_any_pass': sum(v > 0 for v in per_problem),
                'problems_all_attempts_pass': sum(v == 1 for v in per_problem),
                'by_difficulty': {}, 'by_platform': {}, 'terminations': dict(collections.Counter(r['agent_status'] for r in selected)),
                'official_statuses': dict(collections.Counter(r['official_status'] for r in selected)),
                'total_seconds': sum(r['seconds'] for r in selected),
                'median_seconds': statistics.median(r['seconds'] for r in selected) if selected else None,
                'median_correct_seconds': statistics.median(r['seconds'] for r in selected if r['correct']) if passed else None,
                'median_failed_seconds': statistics.median(r['seconds'] for r in selected if not r['correct']) if n > passed else None,
                'actions': sum(r['actions'] for r in selected), 'repairs': sum(r['repairs'] for r in selected),
                'format_errors': sum(r['format_errors'] for r in selected),
                'runs_with_format_errors': sum(r['format_errors'] > 0 for r in selected),
                'command_failures': sum(r['command_failures'] for r in selected),
                'zero_action_runs': sum(r['actions'] == 0 for r in selected),
                'no_recognized_public_test_runs': sum(r['public_tests'] == 0 for r in selected),
                'unchanged_starter_candidates': sum(r['unchanged_starter_candidate'] for r in selected),
                'public_pass_official_failure_runs': sum(r['public_pass_official_failure'] for r in selected),
                'official_pass_without_submitted_status': sum(r['correct'] and r['agent_status'] != 'Submitted' for r in selected),
                'runs_with_command_failures': sum(r['command_failures'] > 0 for r in selected),
                'public_failure_runs': sum(r['public_failures'] > 0 for r in selected),
                **{'public_' + label + '_events': sum(r['public_' + label + '_events'] for r in selected) for label in ('timeout', 'wrong_answer', 'runtime_error', 'unclassified')},
                'public_recoveries': sum(r['public_recovery'] for r in selected),
                'recoveries_officially_correct': sum(r['recovery_to_official_pass'] for r in selected),
                'context_affected_runs': sum(r['context_events'] > 0 for r in selected),
                'offloaded_runs': sum(r['cpu_offload'] for r in selected),
                'residency_snapshot_runs': sum(r['residency_snapshot_available'] for r in selected),
                'prompt_tokens': sum(r['prompt_tokens'] or 0 for r in selected), 'output_tokens': generated,
                'telemetry_complete_runs': sum(bool(r['token_telemetry_complete']) for r in selected),
                'sampler_wire_verified_runs': sum(bool(r['sampler_wire_verified']) for r in selected),
                'maximum_prompt_tokens': max([r['maximum_prompt_tokens'] or 0 for r in selected] + [0]),
                'length_limited_responses': sum(r['length_limited_responses'] for r in selected),
                'prefill_seconds': sum(r['prefill_ns'] or 0 for r in selected) / 1e9,
                'generation_seconds': ns / 1e9,
                'load_seconds': sum(r['load_ns'] or 0 for r in selected) / 1e9,
                'generation_tokens_per_second': generated / (ns / 1e9) if ns else None,
                'output_tokens_per_official_pass': generated / passed if passed else None,
                'agent_seconds_per_official_pass': sum(r['seconds'] for r in selected) / passed if passed else None,
                'duplicate_candidate_pairs': duplicates, 'candidate_pairs_compared': compared}
        for field in ('difficulty', 'platform'):
            for label in sorted({r[field] for r in selected}):
                subset = [r for r in selected if r[field] == label]
                info['by_' + field][label] = {'passed': sum(r['correct'] for r in subset), 'completed': len(subset)}
        summary['models'][model] = info
    for a, b in itertools.combinations(plan['models'], 2):
        differences = []
        a_only = b_only = 0
        for task in tasks:
            aa = [outcomes[task].get((a, r)) for r in range(1, plan['repetitions'] + 1)]
            bb = [outcomes[task].get((b, r)) for r in range(1, plan['repetitions'] + 1)]
            if all(aa + bb):
                av, bv = sum(r['correct'] for r in aa) / len(aa), sum(r['correct'] for r in bb) / len(bb)
                differences.append(av - bv)
                a_only += av > 0 and bv == 0
                b_only += bv > 0 and av == 0
        discordant = a_only + b_only
        pvalue = min(1.0, 2 * sum(math.comb(discordant, k) for k in range(min(a_only, b_only) + 1)) / 2**discordant) if discordant else 1.0
        summary['paired'].append({'a': a, 'b': b, 'complete_problem_pairs': len(differences),
                                  'accuracy_difference': statistics.mean(differences) if differences else None,
                                  'problem_bootstrap_difference_95': interval(differences),
                                  'a_only_problem_success': a_only, 'b_only_problem_success': b_only, 'exploratory_exact_p': pvalue})
    save(batch / 'analysis.json', summary)
    lines = ['# Extended local evaluation: measured comparison', '',
             f"Completed **{len(rows)}/{len(plan['jobs'])}** planned runs; remaining **{summary['remaining']}**.", '',
             f"Profile `{plan['profile']}`; {plan['repetitions']} attempts per problem. All model calls local. No private feedback entered an agent conversation.", '',
             f"Per-attempt limits: {plan.get('actions', 'n/a')} executed actions, {plan.get('repairs', 'n/a')} repair cycles, {plan.get('seconds', 'n/a')} agent seconds; context {plan['profile_config'].get('context', 'n/a')}, response ceiling {plan['profile_config'].get('output_tokens', 'n/a')} tokens. T={plan['profile_config'].get('temperature', 0.0)}. Seeds 2108/2109; Qwen3.5 thinking disabled in the primary comparison.", '',
             'Protocol, commands and full provenance: [README](README.md). Prior-system audit: [AUDIT](AUDIT.md). Configuration experiments: [DEVELOPMENT](DEVELOPMENT.md). Configuration history and sampler correction: [DECISION](DECISION.md).', '',
             '| Model | Official passes | Easy | Medium | Hard | Format-error runs | Context-event runs | Total agent seconds |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for model, info in summary['models'].items():
        fractions = [str(info['by_difficulty'].get(d, {}).get('passed', 0)) + '/' + str(info['by_difficulty'].get(d, {}).get('completed', 0)) for d in ('easy', 'medium', 'hard')]
        lines.append(f"| {model} | {info['passed']}/{info['completed']} | " + ' | '.join(fractions) + f" | {info['runs_with_format_errors']} | {info['context_affected_runs']} | {info['total_seconds']:.1f} |")
    for model, info in summary['models'].items():
        lines += ['', f"{model}: at least one pass on {info['problems_any_pass']}/{info['complete_problem_count']} fully completed problems; every attempt passed on {info['problems_all_attempts_pass']}/{info['complete_problem_count']}. These are empirical coverage counts, not independent repetitions or a population pass@k guarantee."]
    if plan.get('gpu'):
        gpu = next(csv.reader([plan['gpu'].strip()]))
        lines += ['', f"Hardware at freeze: {gpu[0].strip()}, {gpu[2].strip()} GPU memory, driver {gpu[3].strip()}. All three model tags use Q4_K_M weights. Official evaluator and dataset revisions, model digests and Docker image IDs are recorded in the frozen plan; the primary source is also archived by hash."]
    if plan.get('software'):
        software = plan['software']
        packages = software['packages']
        lines += ['', f"Software at freeze: Ollama {software['ollama_project']['version']}; mini-SWE-agent {packages.get('mini-swe-agent')}; LiteLLM {packages.get('litellm')}; Python {plan['python'].split()[0]}. The full installed package map is retained in the plan."]
    if plan['profile_config'].get('sampler'):
        lines += ['', 'Explicit common sampler options: `' + json.dumps(plan['profile_config']['sampler'], sort_keys=True) + '`.', '',
                  'Actual request bodies are retained per attempt. Sampler verification counts: ' + '; '.join(f"{m} {v['sampler_wire_verified_runs']}/{v['completed']}" for m, v in summary['models'].items()) + '.', '',
                  'An earlier tag-default batch was stopped at 111 after discovering unequal model-tag overrides. Those observations are archived separately in TAG_DEFAULT_RESULTS.md and are not pooled here. This configuration correction followed metadata inspection; no previous candidate or private feedback was supplied to the agents. The frozen 24-task set was retained, so it is not claimed to be newly unseen in this corrected run.']
    lines += ['', '## Per-problem paired outcomes', '', 'Cells show official passes/completed attempts; ? indicates unfinished work.', '',
              '| Task | Date | Difficulty | ' + ' | '.join(plan['models']) + ' |',
              '| --- | --- | --- | ' + ' | '.join(['---:'] * len(plan['models'])) + ' |']
    for task, meta in tasks.items():
        cells = []
        for model in plan['models']:
            attempts = [outcomes[task].get((model, r)) for r in range(1, plan['repetitions'] + 1)]
            completed = [a for a in attempts if a]
            cells.append(str(sum(a['correct'] for a in completed)) + '/' + str(len(completed)) + (' ?' if len(completed) < len(attempts) else ''))
        lines.append(f"| {task} | {meta.get('contest_date', '')[:10]} | {meta.get('difficulty', '')} | " + ' | '.join(cells) + ' |')
    lines += ['', '## Workflow reliability and repair', '',
              '| Model | Actions | Repairs | Format failures | Failed non-test commands | Public-failure runs | Public recoveries | Official passes after public failure |',
              '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for model, info in summary['models'].items():
        lines.append(f"| {model} | {info['actions']} | {info['repairs']} | {info['format_errors']} | {info['command_failures']} | {info['public_failure_runs']} | {info['public_recoveries']} | {info['recoveries_officially_correct']} |")
    for model, info in summary['models'].items():
        lines += ['', f"{model}: runs with zero actions: {info['zero_action_runs']}; runs without a recognized public test: {info['no_recognized_public_test_runs']}; unchanged official starters: {info['unchanged_starter_candidates']}. Public passes followed by official failure: {info['public_pass_official_failure_runs']}. Correct preserved candidates with a termination other than Submitted: {info['official_pass_without_submitted_status']}."]
        lines += ['', f"Recognized public-test failure events for {model}: wrong answer after successful candidate execution: {info['public_wrong_answer_events']}; candidate runtime or compile error: {info['public_runtime_error_events']}; six-second timeout: {info['public_timeout_events']}; unclassified: {info['public_unclassified_events']}. These counts include repeated tests of unchanged source."]
    lines += ['', 'A repair is a changed candidate after a recognized public failure; repeated identical writes do not count. Public recovery requires a later passing public test. Private correctness is assessed once after termination, including preserved candidates from action/format limits. Private evaluation never informs another agent action.', '',
              '## Runtime, inference and resources', '',
              '| Model | Median seconds (correct / failed) | Prompt / output tokens | Generation tok/s | Full token telemetry | Max prompt | Length-limit responses | CPU-offloaded runs |',
              '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    def number(value):
        return f'{value:.1f}' if value is not None else 'n/a'
    for model, info in summary['models'].items():
        lines.append(f"| {model} | {number(info['median_correct_seconds'])} / {number(info['median_failed_seconds'])} | {info['prompt_tokens']} / {info['output_tokens']} | {number(info['generation_tokens_per_second'])} | {info['telemetry_complete_runs']}/{info['completed']} | {info['maximum_prompt_tokens']} | {info['length_limited_responses']} | {info['offloaded_runs']} |")
    for model, info in summary['models'].items():
        lines += ['', f"{model} termination counts: `{json.dumps(info['terminations'], sort_keys=True)}`; official statuses: `{json.dumps(info['official_statuses'], sort_keys=True)}`. Platform passes: `{json.dumps(info['by_platform'], sort_keys=True)}`."]
        lines += ['', f"Total prefill/generation/load seconds: {info['prefill_seconds']:.1f} / {info['generation_seconds']:.1f} / {info['load_seconds']:.1f}. Including failed attempts, output tokens per official pass: {number(info['output_tokens_per_official_pass'])}; agent seconds per official pass: {number(info['agent_seconds_per_official_pass'])}. Residency snapshots available for {info['residency_snapshot_runs']}/{info['completed']} runs."]
    lines += ['', 'Agent runtime includes setup, cold model load and public execution; it excludes private judging. Tokens and generation throughput use raw Ollama counts/durations, not wall-clock agent time. Prompt-evaluation counts may reflect cache reuse and are not a count of unique task tokens. Residency comes from post-run allocation snapshots, not continuous peak monitoring. No foreign model workload was permitted at run startup; this is a desktop machine, not a dedicated latency lab.', '',
              '## Paired uncertainty', '',
              'Bootstrap intervals resample fully completed problem clusters (24 in the full plan, both repetitions kept together), 10,000 draws, seed 2108. Coverage counts above show the number available for each model. These descriptive intervals assume exchangeable problems despite purposive selection. They cannot establish generalization to unseen contests.', '',
              '| Model | Accuracy | Problem bootstrap 95% interval | Identical candidate pairs |',
              '| --- | ---: | --- | ---: |']
    for model, info in summary['models'].items():
        bounds = info['problem_bootstrap_95']
        bounds_text = f"{100*bounds[0]:.1f}% to {100*bounds[1]:.1f}%" if bounds else 'n/a'
        lines.append(f"| {model} | {number(100 * info['accuracy_completed']) if info['accuracy_completed'] is not None else 'n/a'}% | {bounds_text} | {info['duplicate_candidate_pairs']}/{info['candidate_pairs_compared']} |")
    for paired in summary['paired']:
        lines += ['', f"{paired['a']} minus {paired['b']}: mean per-problem accuracy difference {paired['accuracy_difference']}; bootstrap 95% interval {paired['problem_bootstrap_difference_95']}; {paired['complete_problem_pairs']} paired problems. At-least-one-success discordants {paired['a_only_problem_success']} versus {paired['b_only_problem_success']}; exploratory two-sided exact p={paired['exploratory_exact_p']:.4g}. This p-value tests the binary any-success outcome, is unadjusted for three comparisons, and does not test the mean accuracy difference."]
    lines += ['', '## Representative trajectories', '',
              'Examples are selected deterministically as the first completed run matching each diagnostic category in schedule order. They illustrate observed behavior rather than establish causes. No candidate source, private input or expected answer is reproduced.', '',
              '| Diagnostic | Task | Model | Repetition | Agent stop | Official status | Actions | Format errors |',
              '| --- | --- | --- | ---: | --- | --- | ---: | ---: |']
    categories = [
        ('No action after format failures', lambda r: r['actions'] == 0 and r['format_errors'] > 0),
        ('Public pass / official failure', lambda r: r['public_pass_official_failure']),
        ('Correct candidate / unfinished workflow', lambda r: r['correct'] and r['agent_status'] != 'Submitted'),
        ('Missing candidate', lambda r: r['official_status'] == 'missing_submission'),
        ('Officially correct after public failure', lambda r: r['recovery_to_official_pass']),
    ]
    for label, predicate in categories:
        example = next((r for r in rows if predicate(r)), None)
        if example:
            r = example
            lines.append(f"| {label} | {r['task_id']} | {r['model']} | {r['repetition']} | {r['agent_status']} | {r['official_status']} | {r['actions']} | {r['format_errors']} |")
    if rows:
        ranking = sorted(summary['models'], key=lambda m: (summary['models'][m]['accuracy_completed'] or 0,
                         -summary['models'][m]['runs_with_format_errors'], -summary['models'][m]['total_seconds']), reverse=True)
        leader = summary['models'][ranking[0]]
        comparisons = []
        for alternative in ranking[1:]:
            other = summary['models'][alternative]
            if leader['completed'] == other['completed'] and leader['completed']:
                pair = next(p for p in summary['paired'] if {p['a'], p['b']} == {ranking[0], alternative})
                alternative_only = pair['b_only_problem_success'] if pair['a'] == ranking[0] else pair['a_only_problem_success']
                problem_word = 'problem' if alternative_only == 1 else 'problems'
                comparisons += ['', f"On the same {leader['completed']} attempts per model, {ranking[0]} passed {leader['passed']} and {alternative} passed {other['passed']}. Format-error runs were {leader['runs_with_format_errors']} versus {other['runs_with_format_errors']}; median time on correct runs was {number(leader['median_correct_seconds'])} versus {number(other['median_correct_seconds'])} seconds. {alternative} solved {alternative_only} fully paired {problem_word} on which the recommended model had no pass. The choice prioritizes observed correctness while retaining these reliability, runtime and task-coverage tradeoffs."]
        costs = ['', f"The recommendation carries substantial failure costs: {leader['terminations'].get('RepeatedFormatError', 0)} repeated-format terminations, {leader['official_statuses'].get('missing_submission', 0)} missing candidates and {leader['length_limited_responses']} length-limited responses. Its total agent time was {leader['total_seconds']/60:.1f} minutes. Including failed runs, agent seconds per official pass were {number(leader['agent_seconds_per_official_pass'])}; the other models' values are reported above. The observed correctness lead does not imply reliable completion on every task."]
        hard = [info['by_difficulty'].get('hard', {'completed': 0, 'passed': 0}) for info in summary['models'].values()]
        hard_note = (['', f"No model passed any of the {sum(h['completed'] for h in hard)} completed hard-task attempts. The observed correctness advantage comes from easy/medium problems. Hard-task performance needs additional configuration research and fresh evaluation; these failures do not establish capability under other workflows or budgets."]
                     if all(h['completed'] and not h['passed'] for h in hard) else [])
        lines += ['', '## Recommendation and uncertainty', '',
                  f"{'Provisional default' if summary['remaining'] else 'Primary operational recommendation'}: **{ranking[0]}** under the measured `{plan['profile']}` configuration, prioritizing official correctness. Reliability and runtime are secondary; short unsuccessful runs do not establish efficiency.", '',
                  *comparisons,
                  *costs,
                  *hard_note,
                  '',
                  f"The two attempts use fresh environments with seeds 2108/2109 and temperature {plan['profile_config'].get('temperature', 0.0)}. Shared tasks, prompts and potentially identical candidates make them dependent. Do not treat 48 attempts as 48 independent problems.", '',
                  'This is a purposive 24-problem infrastructure/capability study, not a statistically conclusive population ranking. The newest compatible official slice dates from 2025; model-training contamination cannot be ruled out. Problems from the same contest may also be correlated. Hard-task and platform subgroups are small. Context truncation, execution budgets, public-feedback semantics and workflow compliance remain potential confounders. More fresh tasks and repeated trials are needed before a broad scientific claim.', '',
                  'The old three-problem pilot and this 24-problem set do not overlap and use different configurations. Their aggregate accuracies are not a controlled scaffold ablation. The development set is also small and selected for interface/repair diagnostics; it does not establish an optimal configuration. The thinking-enabled 9B result is development-only, not an alternate configuration mixed into this primary table.', '',
                  'Difficulty labels come from the dataset and are not independently calibrated across platforms. This benchmark measures standalone Python programming through mini-SWE-agent. Repository bug repair, multi-file changes and frontier-guided interventions require separate evaluation before transferring this operational recommendation to those settings.', '',
                  'Raw private evaluator details and reference audits stay on E: outside agent-visible bundles and Git. `metrics.csv` and `analysis.json` contain complete numerical metrics; trajectories, raw Ollama responses and context logs are retained per attempt.']
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'completed': len(rows), 'planned': len(plan['jobs']), 'remaining': summary['remaining'],
                      'passes': {m: r['passed'] for m, r in summary['models'].items()}, 'report': str(report_path)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    analyze(args.batch, args.report)
