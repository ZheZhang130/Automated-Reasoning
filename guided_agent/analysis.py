"""Per-attempt reliability metrics and paired condition summaries from saved run records.

Only observable evidence is used: commands, observations, token telemetry, judge results.
Hidden-evaluation outcomes enter only as aggregate pass/fail (never case contents).
"""
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

from .common import read_json, write_json

WRITE = re.compile(r"cat\s*>\s*/workspace/solution\.py\s*<<\s*'?\"?(\w+)", re.S)


def _agent_dir(run_dir):
    found = [p for p in run_dir.iterdir() if p.is_dir() and p.name.startswith('agent-')]
    return found[0] if found else None


def comment_stats(command):
    body = command.split('\n', 1)[1] if '\n' in command else ''
    lines = [l for l in body.splitlines() if l.strip()]
    comments = [l for l in lines if l.strip().startswith('#')]
    return len(lines), len(comments)


def attempt_metrics(run_dir, eval_dir=None):
    run_dir = Path(run_dir)
    record = read_json(run_dir / 'result.json')
    agent = _agent_dir(run_dir)
    frozen = read_json(agent / 'result.json') if agent and (agent / 'result.json').exists() else {}
    responses = read_json(agent / 'ollama-responses.json') if agent and (agent / 'ollama-responses.json').exists() else []
    trajectory = read_json(agent / 'trajectory.json') if agent and (agent / 'trajectory.json').exists() else {'messages': []}
    attempts = [json.loads(l) for l in (run_dir / 'attempts.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()] \
        if (run_dir / 'attempts.jsonl').exists() else []
    events = frozen.get('events', [])
    # Map model calls to outcomes: an assistant message followed by a FormatError user message is invalid.
    messages = trajectory.get('messages', [])
    call_valid = []
    for index, message in enumerate(messages):
        if message.get('role') != 'assistant':
            continue
        nxt = messages[index + 1] if index + 1 < len(messages) else {}
        call_valid.append(not (nxt.get('extra', {}).get('interrupt_type') == 'FormatError'))
    first_valid = next((i for i, ok in enumerate(call_valid) if ok), None)
    tokens_to_first = seconds_to_first = None
    if first_valid is not None and len(responses) > first_valid:
        tokens_to_first = sum(r.get('eval_count', 0) for r in responses[:first_valid + 1])
        seconds_to_first = round(sum(r.get('total_duration', 0) for r in responses[:first_valid + 1]) / 1e9, 1)
    writes = [e for e in events if isinstance(e.get('command'), str) and WRITE.search(e['command'])]
    lines = comments = 0
    for event in writes:
        a, b = comment_stats(event['command'])
        lines, comments = lines + a, comments + b
    failed_hashes, repeated_failed_tests, prev_hash, noop_writes = set(), 0, None, 0
    for event in events:
        digest = event.get('source_sha256')
        if event in writes and digest == prev_hash and prev_hash is not None:
            noop_writes += 1
        if event.get('recognized_public_test'):
            if event.get('public_status') != 'pass':
                if digest in failed_hashes:
                    repeated_failed_tests += 1
                failed_hashes.add(digest)
        if digest is not None:
            prev_hash = digest
    statuses = [a['result'].get('status') for a in attempts]
    recovered = any(s != 'pass' for s in statuses) and bool(statuses) and statuses[-1] == 'pass'
    hidden = None
    if eval_dir and (Path(eval_dir) / f"{record['run_id']}.json").exists():
        hidden = read_json(Path(eval_dir) / f"{record['run_id']}.json")
    done = [r.get('done_reason') for r in responses]
    other_cmds = [e for e in events if not e.get('recognized_public_test') and 'returncode' in e and e not in writes]
    return {
        'run_id': record['run_id'], 'task_id': record['task_id'], 'condition': record['condition'],
        'variant': (read_json(run_dir / 'spec.json').get('variant') if (run_dir / 'spec.json').exists() else None),
        'cohort': record.get('cohort'), 'exit_status': record.get('exit_status'), 'raw_exit_status': record.get('raw_exit_status'),
        'correct': None if hidden is None else hidden.get('status') == 'pass',
        'hidden_passed': None if hidden is None else hidden.get('passed'), 'hidden_total': None if hidden is None else hidden.get('total'),
        'hidden_status': None if hidden is None else hidden.get('status'),
        'submitted': record.get('exit_status') == 'submitted', 'candidate': record.get('submission_sha256') is not None,
        'public_tests': len(attempts), 'public_failures': sum(s != 'pass' for s in statuses),
        'public_final_pass': bool(statuses) and statuses[-1] == 'pass', 'public_recovered': recovered,
        'actions': record.get('n_actions'), 'repairs': record.get('n_repairs'), 'model_calls': len(responses),
        'format_errors': sum(not v for v in call_valid), 'length_truncations': done.count('length'),
        'completion_tokens': sum(r.get('eval_count', 0) for r in responses),
        'max_prompt_tokens': max([r.get('prompt_eval_count', 0) for r in responses] + [0]),
        'first_valid_call': None if first_valid is None else first_valid + 1,
        'tokens_to_first_valid': tokens_to_first, 'seconds_to_first_valid': seconds_to_first,
        'source_writes': len(writes), 'noop_writes': noop_writes, 'repeated_failed_tests': repeated_failed_tests,
        'write_comment_ratio': round(comments / lines, 3) if lines else None,
        'other_command_failures': sum(bool(e.get('returncode')) for e in other_cmds),
        'local_coding_seconds': record.get('local_coding_seconds'), 'wall_seconds': record.get('wall_seconds'),
        'guidance_words': (record.get('guidance_provenance') or {}).get('word_count'),
        'guidance_provider': (record.get('guidance_provenance') or {}).get('provider'),
        'guidance_prompt': (record.get('guidance_provenance') or {}).get('prompt_id'),
        'context_events': len(record.get('context_events') or []), 'setup_error': record.get('setup_error'),
        'sampler_wire_verified': record.get('sampler_wire_verified'),
    }


def summarize(batch_dirs, out=None):
    batch_dirs = [Path(b) for b in (batch_dirs if isinstance(batch_dirs, (list, tuple)) else [batch_dirs])]
    rows = []
    for batch in batch_dirs:
        for result in sorted(batch.glob('*/result.json')):
            rows.append(attempt_metrics(result.parent, batch / 'eval'))
    by_condition = defaultdict(list)
    for row in rows:
        by_condition[(row['condition'], row['variant'])].append(row)
    table = {}
    for (condition, variant), items in sorted(by_condition.items(), key=lambda kv: (kv[0][0], kv[0][1] or '')):
        key = condition + (f'/{variant}' if variant else '')
        scored = [r for r in items if r['correct'] is not None]
        table[key] = {'attempts': len(items), 'correct': sum(bool(r['correct']) for r in scored), 'scored': len(scored),
                      'submitted': sum(r['submitted'] for r in items), 'candidate': sum(r['candidate'] for r in items),
                      'public_final_pass': sum(r['public_final_pass'] for r in items),
                      'format_errors': sum(r['format_errors'] for r in items),
                      'length_truncations': sum(r['length_truncations'] for r in items),
                      'repeated_format_exit': sum(r['raw_exit_status'] == 'RepeatedFormatError' for r in items),
                      'completion_tokens': sum(r['completion_tokens'] for r in items),
                      'local_coding_seconds': round(sum(r['local_coding_seconds'] or 0 for r in items), 1)}
    paired = defaultdict(dict)
    for row in rows:
        paired[row['task_id']][row['condition'] + (f"/{row['variant']}" if row['variant'] else '')] = row['correct']
    summary = {'table': table, 'paired_correct': paired, 'rows': rows}
    if out:
        out = Path(out)
        write_json(out.with_suffix('.json'), summary)
        with out.with_suffix('.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else ['run_id'])
            writer.writeheader()
            writer.writerows(rows)
    return summary
