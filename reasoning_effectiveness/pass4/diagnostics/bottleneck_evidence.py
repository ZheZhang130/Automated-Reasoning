"""Bottleneck-audit evidence over every original-agent run of passes 1-3 (A, C, D, E; no ACI, no smoke, no probes).

usage: python reasoning_effectiveness/pass4/diagnostics/bottleneck_evidence.py OUT.json STUDY_ROOT [STUDY_ROOT ...]

For each budget or limit, how often it ended a run or touched a response: exit reasons, format errors, output-cap
and context-cap events, observation clipping, request timeouts, wall time, prompt growth. Counts only; no code,
statements or outputs are written.
"""
import collections
import json
import statistics
import sys
from pathlib import Path

CONTEXT = 16384
OUTPUT_CAP = 4096
OBS_CLIP = 6000


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def original(record):
    return not record.get('aci') and not record.get('smoke') and not record.get('coder') \
        and (record.get('agent_config') or {}).get('id', 'frozen-v6') == 'frozen-v6' \
        and 'probe' not in str(record.get('batch')) and 'integration' not in str(record.get('batch')) \
        and record.get('task_id', '').startswith('lcb-')


def main(out, *studies):
    rows = []
    for study in studies:
        for result in Path(study).glob('runs/*/*/result.json'):
            record = load(result)
            if not original(record) or record.get('condition') not in ('A', 'C', 'D', 'E'):
                continue
            agent_dir = result.parent / ('agent-' + record['run_id'])
            if not (agent_dir / 'ollama-responses.json').exists():
                continue
            responses = load(agent_dir / 'ollama-responses.json')
            frozen = load(agent_dir / 'result.json') if (agent_dir / 'result.json').exists() else {}
            messages = load(agent_dir / 'trajectory.json')['messages'] if (agent_dir / 'trajectory.json').exists() else []
            hidden_path = result.parent.parent / 'eval' / f"{record['run_id']}.json"
            hidden = load(hidden_path).get('status') if hidden_path.exists() else None
            events = [e for e in frozen.get('events') or [] if 'command' in e]
            observations = [m for m in messages if m.get('role') == 'user'][1:]
            cap_events = context_cap = 0
            for r in responses:
                if r.get('done_reason') == 'length':
                    if (r.get('eval_count') or 0) >= OUTPUT_CAP:
                        cap_events += 1
                    elif (r.get('prompt_eval_count') or 0) + (r.get('eval_count') or 0) >= CONTEXT - 8:
                        context_cap += 1
            rows.append({
                'study': Path(study).name, 'batch': result.parent.parent.name, 'task': record['task_id'].split('-')[-1],
                'condition': record['condition'], 'seed': record.get('seed'), 'exit': record.get('exit_status'),
                'raw_exit': record.get('raw_exit_status'), 'error_type': (record.get('frozen_error') or {}).get('error_type'),
                'hidden': hidden, 'program': record.get('submission_sha256') is not None,
                'actions': record.get('n_actions'), 'repairs': record.get('n_repairs'),
                'model_calls': len(responses), 'format_errors': record.get('format_errors') or 0,
                'output_cap_events': cap_events, 'context_cap_events': context_cap,
                'first_truncated': bool(responses) and responses[0].get('done_reason') == 'length',
                'near_cap_responses': sum(1 for r in responses if 3000 <= (r.get('eval_count') or 0) < OUTPUT_CAP),
                'max_prompt_tokens': max([r.get('prompt_eval_count') or 0 for r in responses] + [0]),
                'max_total_tokens': max([(r.get('prompt_eval_count') or 0) + (r.get('eval_count') or 0) for r in responses] + [0]),
                'server_context_events': len(record.get('context_events') or []),
                'observations_over_clip': sum(1 for e in events if len(e.get('output') or '') > OBS_CLIP),
                'command_timeouts': sum(1 for e in events if e.get('returncode') in (124, 137)),
                'public_tests': sum(1 for e in events if e.get('recognized_public_test')),
                'public_pass': any(e.get('public_status') == 'pass' for e in events if e.get('recognized_public_test')),
                'wall_seconds': record.get('wall_seconds'), 'local_coding_seconds': record.get('local_coding_seconds'),
                'eval_seconds': sum((r.get('eval_duration') or 0) for r in responses) / 1e9,
                'output_tokens': sum(r.get('eval_count') or 0 for r in responses),
                'observation_chars_max': max([len(m.get('content') or '') for m in observations] + [0]),
            })
    summary = {}
    by = collections.defaultdict(list)
    for r in rows:
        by[r['condition']].append(r)
        by['all'].append(r)
    for key, group in sorted(by.items()):
        exits = collections.Counter(r['raw_exit'] or r['exit'] for r in group)
        summary[key] = {
            'runs': len(group), 'exits': dict(exits),
            'no_program': sum(not r['program'] for r in group),
            'hidden_pass': sum(r['hidden'] == 'pass' for r in group),
            'runs_with_output_cap_event': sum(r['output_cap_events'] > 0 for r in group),
            'output_cap_events': sum(r['output_cap_events'] for r in group),
            'context_cap_events': sum(r['context_cap_events'] for r in group),
            'first_response_truncated': sum(r['first_truncated'] for r in group),
            'near_cap_responses_3000_4095': sum(r['near_cap_responses'] for r in group),
            'responses': sum(r['model_calls'] for r in group),
            'max_prompt_tokens_max': max(r['max_prompt_tokens'] for r in group),
            'max_prompt_tokens_median': statistics.median(r['max_prompt_tokens'] for r in group),
            'runs_prompt_over_12k': sum(r['max_prompt_tokens'] > 12000 for r in group),
            'server_context_events': sum(r['server_context_events'] for r in group),
            'observations_over_6000_chars': sum(r['observations_over_clip'] for r in group),
            'command_timeouts': sum(r['command_timeouts'] for r in group),
            'action_limit_after_public_pass': sum(r['raw_exit'] in ('ActionLimit', 'LimitsExceeded') and r['public_pass'] for r in group),
            'action_limit_runs': sum(r['raw_exit'] in ('ActionLimit', 'LimitsExceeded') for r in group),
            'deadline_runs': sum(r['raw_exit'] in ('Deadline', 'TimeExceeded') for r in group),
            'request_timeouts': sum((r['error_type'] or '').lower().find('timeout') >= 0 for r in group),
            'wall_seconds_median': statistics.median(r['wall_seconds'] or 0 for r in group),
            'wall_seconds_max': max(r['wall_seconds'] or 0 for r in group),
            'runs_over_500s': sum((r['local_coding_seconds'] or r['wall_seconds'] or 0) > 500 for r in group),
        }
    Path(out).write_text(json.dumps({'summary': summary, 'rows': rows}, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:])
