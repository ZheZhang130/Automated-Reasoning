"""Aggregate prior raw responses and trajectories without emitting candidate code."""
import collections
import csv
import json

from optlib import DATA, ROOT, digest, read, save


def audit():
    batch = DATA.parent / 'eval-v2/batches/extended-24-v6-common'
    rows = [r for r in csv.DictReader((batch / 'metrics.csv').open(encoding='utf-8')) if r['model'] == 'qwen3.5:9b']
    detailed, count = [], collections.Counter()
    hashes = {}
    for row in rows:
        from pathlib import Path
        path = Path(row['attempt'])
        result, trajectory = read(path / 'result.json'), read(path / 'trajectory.json')
        responses, requests = read(path / 'ollama-responses.json'), read(path / 'ollama-requests.json')
        events = result['events']
        sources = [e.get('source_sha256') for e in events if e.get('recognized_public_test')]
        repeated_tests = sum(a == b and bool(a) for a, b in zip(sources, sources[1:]))
        invalid = [m for m in trajectory['messages'] if m.get('extra', {}).get('interrupt_type') == 'FormatError']
        invalid_lengths = sum(m.get('extra', {}).get('response', {}).get('choices', [{}])[0].get('finish_reason') == 'length' for m in invalid)
        length_responses = [r for r in responses if r.get('done_reason') == 'length']
        length_with_fence = sum('```' in r.get('message', {}).get('content', '') for r in length_responses)
        item = {k: row[k] for k in ('task_id', 'seed', 'agent_status', 'official_status', 'seconds', 'output_tokens', 'model_calls', 'actions', 'public_recovery')}
        item.update(format_errors=len(invalid), length_responses=len(length_responses), invalid_length_turns=invalid_lengths,
                    length_with_fence=length_with_fence, repeated_identical_source_public_tests=repeated_tests,
                    raw_requests=len(requests), raw_responses=len(responses), maximum_prompt_tokens=result['inference']['maximum_prompt_tokens'])
        detailed.append(item)
        count.update({'runs': 1, 'correct': int(row['correct']), 'format_errors': len(invalid), 'length_responses': len(length_responses),
                      'invalid_length_turns': invalid_lengths, 'repeated_identical_source_public_tests': repeated_tests,
                      'zero_actions': int(row['actions']) == 0, 'missing_submission': row['official_status'] == 'missing_submission',
                      'public_pass_official_failure': row['public_pass_official_failure'] == 'True',
                      'context_affected_runs': int(row['context_events']) > 0,
                      'failed_output_tokens': int(row['output_tokens']) if not int(row['correct']) else 0})
        for filename in ('result.json', 'trajectory.json', 'ollama-requests.json', 'ollama-responses.json', 'private_evaluation.json'):
            hashes[str(path / filename)] = digest(path / filename)
    report = {'baseline': str(batch), 'counts': dict(count), 'runs': detailed,
              'classification': {'interface': 'Length-limited generations, invalid command fences, no executed actions, missing candidates.',
                  'reasoning_or_validation': 'Candidates failing official tests; passing examples does not establish hidden correctness. No benchmark-specific hints are supplied.',
                  'infrastructure': 'Native history omission is reproduced separately; original primary used text, so cannot explain its failures. Context truncation is separately measured.'}}
    save(ROOT / 'baseline_audit.json', report)
    save(DATA / 'baseline-evidence-sha256.json', hashes)
    print(json.dumps(report['counts']))


if __name__ == '__main__':
    audit()
