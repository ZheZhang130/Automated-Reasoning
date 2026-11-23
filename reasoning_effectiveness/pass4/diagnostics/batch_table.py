"""Per-attempt metrics for pass-4 batches (reads run records, trajectories and hidden results; writes JSON).

usage: python reasoning_effectiveness/pass4/diagnostics/batch_table.py OUT.json BATCH_DIR [BATCH_DIR ...]

Every number comes from the run record, the captured Ollama responses, the trajectory or the hidden-evaluation
file. Nothing about hidden model reasoning is inferred.
"""
import json
import re
import sys
from pathlib import Path

WRITE = re.compile(r'(?:cat|tee)\s*>?\s*/workspace/solution\.py|>\s*/workspace/solution\.py')
TEST = re.compile(r'^\s*python(?:3)?\s+(?:-I\s+)?/public/check\.py\s*$')


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def attempt_metrics(result_path):
    record = load(result_path)
    run_dir = Path(result_path).parent
    batch = run_dir.parent
    hidden_path = batch / 'eval' / f"{record['run_id']}.json"
    hidden = load(hidden_path) if hidden_path.exists() else {}
    agent_dir = run_dir / ('agent-' + record['run_id'])
    responses = load(agent_dir / 'ollama-responses.json') if (agent_dir / 'ollama-responses.json').exists() else []
    trajectory = load(agent_dir / 'trajectory.json')['messages'] if (agent_dir / 'trajectory.json').exists() else []
    assistant = [m.get('content') or '' for m in trajectory if m.get('role') == 'assistant']
    repeats = sum(1 for a, b in zip(assistant, assistant[1:]) if a == b)
    done = [r.get('done_reason') for r in responses]
    events = record.get('events') or []
    frozen = load(agent_dir / 'result.json') if (agent_dir / 'result.json').exists() else {}
    events = frozen.get('events') or []
    actions = [e for e in events if 'command' in e]
    first_test = next((i + 1 for i, e in enumerate(actions) if e.get('recognized_public_test')), None)
    writes = [e for e in actions if isinstance(e.get('command'), str) and WRITE.search(e['command'])]
    failed = set()
    rewrites_of_failed = 0
    for e in actions:
        if e.get('recognized_public_test') and e.get('public_status') != 'pass' and e.get('source_sha256'):
            failed.add(e['source_sha256'])
        elif e in writes and e.get('source_sha256') in failed:
            rewrites_of_failed += 1
    public = [e for e in actions if e.get('recognized_public_test')]
    thinking_chars = sum(len((r.get('message') or {}).get('thinking') or '') for r in responses)
    sp = record.get('self_plan') or {}
    inference = record.get('inference') or {}
    out = {
        'run': run_dir.name, 'run_id': record['run_id'], 'task': record['task_id'].split('-')[-1],
        'condition': record['condition'], 'agent': (record.get('agent_config') or {}).get('id', 'frozen-v6'),
        'seed': record.get('seed'), 'exit': record.get('exit_status'), 'raw_exit': record.get('raw_exit_status'),
        'setup_error': record.get('setup_error'),
        'hidden': hidden.get('status'), 'hidden_passed': hidden.get('passed'), 'hidden_total': hidden.get('total'),
        'program': record.get('submission_sha256') is not None, 'actions': record.get('n_actions'),
        'repairs': record.get('n_repairs'), 'model_calls': record.get('model_calls'),
        'format_errors': record.get('format_errors'),
        'truncated_responses': done.count('length'), 'first_response_truncated': bool(done) and done[0] == 'length',
        'first_response_tokens': responses[0].get('eval_count') if responses else None,
        'first_public_test_action': first_test, 'public_tests': len(public),
        'public_pass': any(e.get('public_status') == 'pass' for e in public),
        'writes': len(writes), 'rewrites_of_failed_candidate': rewrites_of_failed, 'exact_repeats': repeats,
        'prompt_tokens': inference.get('prompt_eval_count'), 'output_tokens': inference.get('eval_count'),
        'max_prompt_tokens': inference.get('maximum_prompt_tokens'),
        'eval_seconds': (inference.get('eval_duration') or 0) / 1e9,
        'prompt_eval_seconds': (inference.get('prompt_eval_duration') or 0) / 1e9,
        'thinking_chars': thinking_chars, 'context_events': len(record.get('context_events') or []),
        'self_plan_tokens': sp.get('completion_tokens'), 'self_plan_prompt_tokens': sp.get('prompt_tokens'),
        'self_plan_seconds': sp.get('wall_seconds'), 'self_plan_truncated': sp.get('truncated'),
        'self_plan_eval_seconds': sp.get('eval_seconds'),
        'wall_seconds': record.get('wall_seconds'), 'local_coding_seconds': record.get('local_coding_seconds'),
        'sampler_wire_verified': record.get('sampler_wire_verified'),
        'frozen_files_verified': (record.get('frozen_verification') or {}).get('frozen_files_verified'),
        'model_digest_ok': (record.get('model_digest') or '').startswith('56671c2a'),
        'receipts': (record.get('receipts') or {}).get('count'),
        'diagnosis_triggered': (record.get('diagnosis') or {}).get('trigger_observed'),
        'diagnosis_delivered': (record.get('diagnosis') or {}).get('delivered'),
        'contract_checks': record.get('contract_checks_summary'),
    }
    out['local_output_tokens_total'] = (out['output_tokens'] or 0) + (out['self_plan_tokens'] or 0)
    return out


def main(out, *batches):
    rows = []
    for batch in batches:
        for result in sorted(Path(batch).glob('*/result.json')):
            if '.incomplete-' in result.parent.name:
                continue
            rows.append(attempt_metrics(result))
    Path(out).write_text(json.dumps(rows, indent=1) + '\n', encoding='utf-8', newline='\n')
    for r in rows:
        print(f"{r['task']:9} {r['condition']} {r['agent']:15} {r['exit']:12} {str(r['hidden']):18} prog={int(r['program'])} "
              f"acts={r['actions']:>2} trunc={r['truncated_responses']}{'*' if r['first_response_truncated'] else ' '} "
              f"rep={r['exact_repeats']} rwf={r['rewrites_of_failed_candidate']} out={r['local_output_tokens_total']:>6} "
              f"wall={r['wall_seconds']}")


if __name__ == '__main__':
    main(*sys.argv[1:])
