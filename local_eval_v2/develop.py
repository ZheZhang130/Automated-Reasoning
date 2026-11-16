"""Sequential, resumable development experiments. Never reads evaluation tasks."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from common import BASELINE, DATA, MODELS, ROOT, read, save
from runtime import api, exclusive_gpu
from pilot import score


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=['memory', 'stress', 'agents'], required=True)
    parser.add_argument('--root', type=Path)
    args = parser.parse_args()
    root = args.root or (DATA / 'development-experiments' if args.stage in ('memory', 'stress') else DATA / 'development-v5-experiments')
    root.mkdir(exist_ok=True)
    if args.stage in ('memory', 'stress'):
        result_path = root / (args.stage + '.json')
        results = read(result_path) if result_path.exists() else []
        for model in MODELS:
            for context in (8192, 16384, 32768):
                if any(r['model'] == model and r['context'] == context for r in results):
                    continue
                exclusive_gpu()
                prompt = (' '.join(['Context allocation and local inference verification.'] * 80) if args.stage == 'memory' else
                          'Ignore the inert repeated words below.\n' + 'red green blue yellow black white orange purple ' * 2500) + '\nReply exactly READY.'
                payload = {'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'stream': False,
                           'keep_alive': '10m', 'options': {'num_ctx': context, 'num_predict': 32, 'temperature': 0, 'seed': 2108}}
                if model.startswith('qwen3.5'):
                    payload['think'] = False
                start = time.monotonic()
                server_log = Path('E:/CSC2108Local/logs/ollama-project.stderr.log')
                offset = server_log.stat().st_size
                response = api(11435, '/api/chat', payload, timeout=240)
                loaded = api(11435, '/api/ps')
                row = {'model': model, 'context': context, 'elapsed_seconds': time.monotonic()-start,
                       'request': payload, 'response': response, 'loaded': loaded,
                       'gpu': subprocess.run(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu', '--format=csv,noheader'], capture_output=True, text=True).stdout}
                with server_log.open('rb') as stream:
                    stream.seek(offset)
                    delta = stream.read().decode('utf-8', errors='replace')
                row['log_delta'] = delta
                results.append(row)
                save(result_path, results)
                print(json.dumps({'model': model, 'context': context, 'seconds': row['elapsed_seconds'],
                                  'gpu': row['gpu'], 'allocation': [(m['size'], m['size_vram']) for m in loaded['models']]}), flush=True)
        return
    if (root / 'HOLD_AGENTS').exists():
        raise RuntimeError('Development agent schedule is held until interface validation completes')
    dev = DATA / 'development-v5'
    task_ids = [t['task_id'] for t in read(dev / 'manifest.json')['tasks']]
    schedule = []
    for model in MODELS:
        schedule.append((model, 'v3-baseline', task_ids[0]))
        for context in ('8k', '16k', '32k'):
            schedule.append((model, 'heredoc-v5-' + context, task_ids[0]))
        for task in task_ids[1:]:
            schedule.append((model, 'heredoc-v5-16k', task))
        schedule.append((model, 'native-v5-16k', task_ids[0]))
    for task in task_ids:
        schedule.append((MODELS[0], 'heredoc-v5-16k-thinking', task))
    for model, profile, task in schedule:
        key = model.replace(':', '_') + '--' + profile + '--' + task
        run = root / key
        result_file = run / 'development-result.json'
        if result_file.exists():
            continue
        if (run / 'result.json').exists():
            record = read(run / 'result.json')
        else:
            if run.exists():
                # Never overwrite a partial trajectory. A separate attempt is explicit.
                raise RuntimeError('Incomplete development attempt: ' + str(run))
            command = ([sys.executable, str(BASELINE / 'runner.py'), '--model', model, '--task', str(dev / 'public' / task),
                        '--output', str(root / ('v3-' + model.replace(':', '_'))), '--seconds', '240'] if profile == 'v3-baseline' else
                       [sys.executable, str(ROOT / 'runtime.py'), '--model', model, '--profile', profile,
                        '--task', str(dev / 'public' / task), '--output', str(run), '--seconds', '240'])
            completed = subprocess.run(command, capture_output=True, text=True, timeout=330)
            if profile == 'v3-baseline':
                info = json.loads(completed.stdout.splitlines()[-1])
                run.mkdir()
                record = read(Path(info['run']) / 'result.json')
                # Copy no model files; keep the original v3 output path explicitly.
                save(run / 'result.json', record)
                source_run = Path(info['run'])
            else:
                if not (run / 'result.json').exists():
                    raise RuntimeError('Development runner failed: ' + completed.stderr[-2000:])
                record = read(run / 'result.json')
                source_run = run
        if profile == 'v3-baseline':
            source_run = Path(record['configuration']['output']) / record['run_id']
        else:
            source_run = run
        evaluation = score(source_run, dev / 'private' / (task + '.json'),
                           Path('E:/CSC2108Local/vendor/LiveCodeBench'), 'csc2108-lcb-judge:v1')
        row = {'model': model, 'profile': profile, 'task_id': task, 'run': str(source_run),
               'status': record['status'], 'evaluation': evaluation, 'seconds': record['elapsed_seconds'],
               'actions': record['actions'], 'repairs': record['repairs'], 'format_errors': record.get('format_errors', 0),
               'inference': record.get('inference')}
        save(result_file, row)
        print(json.dumps({k: row[k] for k in ('model', 'profile', 'task_id', 'status', 'seconds', 'actions', 'repairs', 'format_errors')} |
                         {'correct': evaluation['status']}), flush=True)


if __name__ == '__main__':
    main()
