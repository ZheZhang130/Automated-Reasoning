"""What precedes an exact repeat of the agent's previous response? (observable trajectory text only)

usage (repository root):  python -m reasoning_effectiveness.pass3.diagnostics.repeat_context OUT.json STUDY ...

For every assistant message that is byte-identical to the assistant message immediately before it, classify the
user message in between: an empty successful command acknowledgement (``<returncode>0</returncode>`` with no
output), a public-test report, an ACI note, a format-error message, or other command output. Also measure
how long the identical streak lasts and how the run ends. Original agent, ACI and probe runs are separated.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

EMPTY_ACK = re.compile(r'^\s*<returncode>0</returncode>\s*$')


def kind_of(observation):
    text = observation or ''
    if EMPTY_ACK.match(text):
        return 'empty_success_ack'
    if 'PUBLIC TESTS' in text:
        return 'public_report'
    if '[harness]' in text:
        return 'aci_note'
    if text.startswith('Rejected:'):
        return 'format_error'
    return 'other_output'


def main(out, *studies):
    counts = defaultdict(Counter)
    streaks = defaultdict(list)
    for study in map(Path, studies):
        for result in sorted(study.glob('runs/*/*/result.json')):
            run_dir = result.parent
            if run_dir.parent.name.startswith(('integration', 'b-')) or 'incomplete' in run_dir.name:
                continue
            record = json.loads(result.read_text(encoding='utf-8'))
            if record.get('coder') or str(record.get('coding_model', '')).startswith('frontier'):
                continue
            agents = sorted(run_dir.glob('agent-*'))
            if not agents or not (agents[0] / 'trajectory.json').exists():
                continue
            group = ('aci' if record.get('aci') else 'probe' if run_dir.parent.name.startswith('probe') else 'original')
            key = f"{group}|{record.get('condition')}"
            messages = json.loads((agents[0] / 'trajectory.json').read_text(encoding='utf-8'))['messages']
            last_assistant, between, previous_between, streak = None, None, None, 0
            for message in messages:
                if message.get('role') == 'assistant':
                    text = message.get('content') or ''
                    if last_assistant is not None and text == last_assistant:
                        counts[key][kind_of(between)] += 1
                        # the decisive suffix is self-similar when the observation equals the one before
                        counts[key]['observation_identical_to_previous'] += between == previous_between
                        streak += 1
                    else:
                        if streak:
                            streaks[key].append(streak)
                        streak = 0
                    last_assistant, previous_between, between = text, between, None
                elif message.get('role') == 'user' and last_assistant is not None:
                    between = message.get('content')
            if streak:
                streaks[key].append(streak)
            counts[key]['runs'] += 1
            counts[key]['runs_with_repeat'] += bool(streaks[key] and streak) or any(True for _ in [])
    summary = {k: dict(v) | {'streaks': len(streaks[k]), 'longest_streak': max(streaks[k], default=0),
                             'repeats_in_streaks_of_3_or_more': sum(s for s in streaks[k] if s >= 3)}
               for k, v in counts.items()}
    Path(out).write_text(json.dumps(summary, indent=1) + '\n', encoding='utf-8', newline='\n')
    for k in sorted(summary):
        print(k, json.dumps(summary[k]))


if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:])
