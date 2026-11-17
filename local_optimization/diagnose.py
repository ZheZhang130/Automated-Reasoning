"""Non-benchmark mechanism checks and Qwen-only context allocation probes."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from optlib import DATA, GPU_LOCK, MODEL, ROOT, Lock, read, save
from runtime import api, exclusive_gpu


def contexts():
    path = DATA / 'diagnostics/context-allocation.json'
    if path.exists():
        raise ValueError('Probe output already exists')
    records = []
    with Lock(GPU_LOCK):
        for context in (32768, 65536, 131072):
            exclusive_gpu()
            response = api(11435, '/api/chat', {'model': MODEL, 'messages': [{'role': 'user', 'content': 'Reply READY.'}],
                'think': False, 'stream': False, 'keep_alive': '10m', 'options': {'num_ctx': context, 'num_predict': 1, 'temperature': 0, 'seed': 2108}}, timeout=180)
            records.append({'context': context, 'raw': response, 'ps': api(11435, '/api/ps'),
                'gpu': subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu', '--format=csv,noheader'], text=True).strip()})
            save(path, records)
            print(json.dumps(records[-1]), flush=True)
            model = records[-1]['ps']['models'][0]
            if model['size_vram'] < model['size']:
                break
        exclusive_gpu()


def fixtures():
    for task in ('dev-negative-squares', 'dev-functional-distinct'):
        for profile in ('native-stock-16k-4k', 'native-fixed-16k-4k'):
            output = DATA / 'diagnostics' / (task + '--' + profile)
            if (output / 'result.json').exists():
                continue
            subprocess.run([sys.executable, str(ROOT / 'runtime_opt.py'), '--task', str(DATA.parent / 'eval-v2/development-v5/public' / task),
                            '--output', str(output), '--profile', profile], check=True)
            result = read(output / 'result.json')
            if result.get('status') == 'InfrastructureError':
                raise RuntimeError(str(result.get('error')))
            if profile.startswith('native-fixed') and not result.get('native_history_wire_verified'):
                raise RuntimeError('Native history invariant failed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['contexts', 'fixtures'])
    args = parser.parse_args()
    contexts() if args.action == 'contexts' else fixtures()
