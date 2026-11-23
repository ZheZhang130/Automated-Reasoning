"""What causes the format errors that end runs (original agent, passes 1-3)?

usage: python reasoning_effectiveness/pass4/diagnostics/format_errors.py OUT.json STUDY_ROOT [...]

A FormatError message carries the frozen template; its length branch is present exactly when the response hit the
generation limit (``finish_reason == 'length'``). Counts only.
"""
import collections
import json
import sys
from pathlib import Path

from bottleneck_evidence import load, original

LENGTH_MARK = 'The generation limit was reached'


def main(out, *studies):
    counts = collections.Counter()
    per_run = []
    for study in studies:
        for result in Path(study).glob('runs/*/*/result.json'):
            record = load(result)
            if not original(record) or record.get('condition') not in ('A', 'C', 'D', 'E'):
                continue
            path = result.parent / ('agent-' + record['run_id']) / 'trajectory.json'
            if not path.exists():
                continue
            messages = load(path)['messages']
            errors = [m for m in messages if (m.get('extra') or {}).get('interrupt_type') == 'FormatError']
            length = sum(LENGTH_MARK in (m.get('content') or '') for m in errors)
            counts['runs'] += 1
            counts['format_errors'] += len(errors)
            counts['length_format_errors'] += length
            counts['other_format_errors'] += len(errors) - length
            final = record.get('raw_exit_status') == 'RepeatedFormatError'
            if final:
                counts['repeated_format_error_runs'] += 1
                last3 = errors[-3:]
                counts['terminal_triples_all_length'] += all(LENGTH_MARK in (m.get('content') or '') for m in last3)
            if errors and not final:
                counts['runs_recovering_after_a_format_error'] += 1
            per_run.append({'run': result.parent.name, 'condition': record['condition'], 'format_errors': len(errors),
                            'length': length, 'repeated_format_error': final})
    Path(out).write_text(json.dumps({'counts': counts, 'runs': per_run}, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(counts, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:])
