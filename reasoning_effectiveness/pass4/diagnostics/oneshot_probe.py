"""Agent-versus-model diagnostic (pass 4, Phase I 5.5): one direct Qwen call per task, no agent, no tools.

usage: python reasoning_effectiveness/pass4/diagnostics/oneshot_probe.py TASK_ID [TASK_ID ...]
       (environment: CSC2108_STUDY_ROOT = the pass-4 study root)

Not a condition and not a benchmark. It separates "the model cannot find a working algorithm" from "the model
can, but not through the agent's action protocol": the same model, frozen sampler and seed get the statement and
one instruction to return a complete program; the output allowance is 8,192 tokens so that deliberation can finish.
The program is taken from the LAST closed ```python block (no repair, no joining) and judged only by the team
judge inside its container (public suite first, then hidden). Raw responses stay in the study root.
"""
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from guided_agent import backend  # noqa: E402
from guided_agent.common import MODEL, read_json, settings, sha256_bytes, sha256_text, study_root, utc_now, write_json  # noqa: E402
from guided_agent.tasks import load_statement  # noqa: E402

SYSTEM = ('You are an expert competitive programmer. Solve the problem below in Python 3.11. The program must read '
          'standard input and write standard output. Think as much as you need, then give the complete final program '
          'in one ```python code block at the end of your answer.')
OPTIONS = {'top_k': 40, 'top_p': 0.9, 'min_p': 0.0, 'repeat_penalty': 1.0, 'repeat_last_n': 64, 'presence_penalty': 0.0,
           'frequency_penalty': 0.0, 'num_ctx': 16384, 'num_predict': 8192, 'temperature': 0.2, 'seed': 2108}
BLOCK = re.compile(r'```(?:python|py)\s*\n(.*?)\n```', re.S)


def main(task_ids):
    import requests
    from local_agent.platform_support import model_lock
    host = settings('auto')
    study = study_root(host)
    out_dir = study / 'probes' / 'oneshot'
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    with model_lock(host):
        if requests.get('http://127.0.0.1:11434/api/ps', timeout=5).json().get('models'):
            raise SystemExit('foreign models are loaded on the app endpoint; not starting')
        for task_id in task_ids:
            statement = load_statement(study, task_id)
            body = {'model': MODEL, 'stream': False, 'think': False, 'keep_alive': '10m', 'options': OPTIONS,
                    'messages': [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': statement}]}
            started = time.monotonic()
            raw = requests.post('http://127.0.0.1:11435/api/chat', json=body, timeout=600).json()
            wall = time.monotonic() - started
            text = (raw.get('message') or {}).get('content') or ''
            blocks = BLOCK.findall(text)
            code = (blocks[-1] + '\n').encode() if blocks else None
            write_json(out_dir / f'{task_id}.json', {'request_sha256': sha256_text(json.dumps(body, sort_keys=True)),
                                                     'response': raw, 'wall_seconds': wall, 'utc': utc_now()})
            rows.append({'task_id': task_id, 'done_reason': raw.get('done_reason'), 'eval_count': raw.get('eval_count'),
                         'prompt_eval_count': raw.get('prompt_eval_count'), 'wall_seconds': round(wall, 2),
                         'eval_seconds': (raw.get('eval_duration') or 0) / 1e9, 'python_blocks': len(blocks),
                         'program_sha256': sha256_bytes(code) if code else None})
            if code:
                (out_dir / f'{task_id}.py').write_bytes(code)
    for suite in ('public', 'hidden'):
        judge = backend.judge_client(study, suite)
        judge.up()
        for row in rows:
            if row['program_sha256']:
                result = judge.run(row['task_id'], (out_dir / f"{row['task_id']}.py").read_bytes())
                row[suite] = {k: result.get(k) for k in ('status', 'passed', 'total', 'verdict_counts')}
            else:
                row[suite] = {'status': 'missing_submission'}
    write_json(out_dir / 'summary.json', rows)
    for row in rows:
        print(json.dumps({k: row.get(k) for k in ('task_id', 'done_reason', 'eval_count', 'wall_seconds', 'python_blocks')}
                         | {'public': row['public'].get('status'), 'hidden': row['hidden'].get('status'),
                            'hidden_passed': row['hidden'].get('passed')}))


if __name__ == '__main__':
    main(sys.argv[1:])
