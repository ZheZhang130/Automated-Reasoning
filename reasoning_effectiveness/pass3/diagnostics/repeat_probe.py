"""Model-only probe of the identical-rewrite fixed point (no agent, no sandbox, no judge).

usage (repository root, Windows backend, project Ollama on 11435):
  python -m reasoning_effectiveness.pass3.diagnostics.repeat_probe OUT.json STUDY ...

For every run of the ORIGINAL agent, find each streak start: model response k that is byte-identical to response
k-1 (both complete). The exact request body that produced response k was captured by the frozen runtime
(``ollama-requests.json``: messages, options, seed). Re-send it to the project Ollama endpoint:

* ``seed`` unchanged      -> determinism check (should reproduce the repeat);
* three different seeds  -> does sampling at temperature 0.2 escape the fixed point?

Each reply is compared with the repeated response (identical / different) and its command is classified
(rewrites solution.py, runs the public test, other). Requests run under the project GPU lock and only when no
foreign model is loaded on the app endpoint. No program is executed.
"""
import json
import re
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

ENDPOINT = 'http://127.0.0.1:11435/api/chat'
SEEDS = (3001, 3002, 3003)
WRITE = re.compile(r'(?:cat|tee)\s*>?\s*/workspace/solution\.py|>\s*/workspace/solution\.py')
TEST = re.compile(r'python\s+-I\s+/public/check\.py')


def action_kind(text):
    if TEST.search(text or ''):
        return 'public_test'
    if WRITE.search(text or ''):
        return 'write'
    return 'other'


def chat(body, timeout=240):
    request = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    return payload, round(time.monotonic() - started, 2)


def streak_starts(study):
    for result in sorted(Path(study).glob('runs/*/*/result.json')):
        run_dir = result.parent
        if run_dir.parent.name.startswith(('integration', 'b-', 'probe')) or 'incomplete' in run_dir.name:
            continue
        record = json.loads(result.read_text(encoding='utf-8'))
        if record.get('aci') or record.get('coder'):
            continue
        agents = sorted(run_dir.glob('agent-*'))
        if not agents or not (agents[0] / 'ollama-requests.json').exists():
            continue
        requests = json.loads((agents[0] / 'ollama-requests.json').read_text(encoding='utf-8'))
        responses = json.loads((agents[0] / 'ollama-responses.json').read_text(encoding='utf-8'))
        texts = [(r.get('message') or {}).get('content') or '' for r in responses]
        for k in range(1, min(len(texts), len(requests))):
            done = responses[k].get('done_reason') == 'stop' and responses[k - 1].get('done_reason') == 'stop'
            if done and texts[k] == texts[k - 1] and (k < 2 or texts[k - 1] != texts[k - 2]):
                yield {'run': f'{Path(study).name}/{run_dir.parent.name}/{run_dir.name}', 'task_id': record['task_id'],
                       'condition': record['condition'], 'request_index': k, 'repeated_kind': action_kind(texts[k])}, \
                    requests[k], texts[k]


def main(out, *studies):
    from local_agent.platform_support import Settings, model_lock
    from guided_agent.__main__ import foreign_models
    rows, seen = [], set()
    with model_lock(Settings.load('windows')):
        if foreign_models():
            raise SystemExit('foreign models loaded on the app endpoint; not probing')
        for study in studies:
            for meta, body, repeated in streak_starts(study):
                key = json.dumps(body, sort_keys=True)  # token-identical reruns (pass 2 of pass 1) probed once
                if key in seen:
                    continue
                seen.add(key)
                row = dict(meta, variants=[])
                for seed in (body['options'].get('seed'),) + SEEDS:
                    variant = json.loads(json.dumps(body))
                    variant['options']['seed'] = seed
                    variant['stream'] = False
                    payload, seconds = chat(variant)
                    text = (payload.get('message') or {}).get('content') or ''
                    row['variants'].append({'seed': seed, 'original_seed': seed == body['options'].get('seed'),
                                            'identical_to_repeat': text == repeated, 'kind': action_kind(text),
                                            'done_reason': payload.get('done_reason'), 'tokens': payload.get('eval_count'),
                                            'seconds': seconds})
                rows.append(row)
                print(json.dumps({k: row[k] for k in ('run', 'request_index', 'repeated_kind')} |
                                 {'identical': [v['identical_to_repeat'] for v in row['variants']]}), flush=True)
    summary = Counter()
    for row in rows:
        original, others = row['variants'][0], row['variants'][1:]
        summary['streak_starts'] += 1
        summary['original_seed_reproduces_repeat'] += original['identical_to_repeat']
        summary['resamples'] += len(others)
        summary['resamples_identical'] += sum(v['identical_to_repeat'] for v in others)
        summary['resamples_running_public_test'] += sum(v['kind'] == 'public_test' for v in others)
        summary['streak_starts_escaped_by_any_seed'] += any(not v['identical_to_repeat'] for v in others)
    data = {'summary': dict(summary), 'rows': rows}
    Path(out).write_text(json.dumps(data, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(data['summary']))


if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:])
