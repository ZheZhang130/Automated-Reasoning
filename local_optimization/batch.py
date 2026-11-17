"""Frozen-source, sequential, resumable paired local optimization batches."""
import argparse
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from optlib import BASELINE, DATA, GPU_LOCK, JUDGE, MODEL, MODEL_DIGEST, REPO, ROOT, V2, VENDOR, Lock, alive, digest, on_e, read, save, sources
from runtime import api
from dataset import EVALUATOR
import runner as sandbox
from pilot import score


def pinned_vendor():
    revision = subprocess.check_output(['git', '-C', str(VENDOR), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(VENDOR), 'status', '--porcelain'], text=True)
    if revision != EVALUATOR or dirty:
        raise RuntimeError('Official evaluator must be clean at its pinned revision')


def freeze(args, batch):
    manifest_path = args.manifest.resolve(strict=True)
    manifest = read(manifest_path)
    profiles = read(ROOT / 'profiles.json')
    for profile in args.profiles:
        if profile not in profiles:
            raise ValueError('Unknown profile ' + profile)
    tasks = manifest['tasks']
    if args.tasks:
        tasks = [t for t in tasks if t['task_id'] in args.tasks]
        if len(tasks) != len(args.tasks):
            raise ValueError('Unknown task filter')
    pinned_vendor()
    with Lock(GPU_LOCK):
        if api(11434, '/api/ps')['models']:
            raise RuntimeError('Foreign Ollama workload active')
        images = {image: sandbox.isolation_preflight(image, Path('E:/DockerDesktop')) for image in (sandbox.IMAGE, JUDGE)}
    tags = api(11435, '/api/tags')['models']
    if next(t['digest'] for t in tags if t['name'] == MODEL) != MODEL_DIGEST:
        raise RuntimeError('Qwen9 model digest changed')
    specs = {}
    for task in tasks:
        public = manifest_path.parent / 'public' / task['task_id']
        private = manifest_path.parent / 'evaluator_private' / (task['task_id'] + '.json')
        if {p.name: digest(p) for p in public.iterdir()} != task['public_sha256'] or digest(private) != task['private_row_sha256']:
            raise RuntimeError('Task differs from frozen manifest')
        specs[task['task_id']] = {'public': str(public), 'private': str(private), 'metadata': task}
    jobs = []
    for index, task in enumerate(tasks):
        for repetition, seed in enumerate(args.seeds, 1):
            offset = (index + repetition - 1) % len(args.profiles)
            for profile in args.profiles[offset:] + args.profiles[:offset]:
                jobs.append({'key': task['task_id'] + '--' + profile + '--s' + str(seed), 'task_id': task['task_id'], 'model': MODEL,
                             'profile': profile, 'seed': seed, 'repetition': repetition})
    hashes = sources()
    for relative, checksum in hashes.items():
        source, destination = REPO / relative, batch / 'frozen-source' / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if digest(destination) != checksum:
            raise RuntimeError('Source changed during freeze')
    plan = {'manifest_path': str(manifest_path), 'manifest_sha256': digest(manifest_path), 'manifest': manifest,
            'profiles': {p: profiles[p] for p in args.profiles}, 'jobs': jobs, 'tasks': specs,
            'actions': 20, 'repairs': 3, 'seconds': args.seconds, 'model_digest': MODEL_DIGEST,
            'source_sha256': hashes, 'images': images, 'evaluator_revision': EVALUATOR,
            'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
            'python': sys.version, 'packages': {p: importlib.metadata.version(p) for p in ('mini-swe-agent', 'litellm', 'pydantic')},
            'ollama': api(11435, '/api/version'), 'created_unix': time.time(),
            'gpu_hardware': subprocess.check_output(['nvidia-smi', '--query-gpu=name,uuid,memory.total,driver_version', '--format=csv,noheader'], text=True),
            'installed_ollama_adapter_sha256': digest(Path(importlib.util.find_spec('litellm').origin).parent / 'llms/ollama/chat/transformation.py')}
    save(batch / 'plan.json', plan)
    return plan


def consumed():
    tokens, ns = 0, 0
    for path in DATA.rglob('result.json'):
        inf = read(path).get('inference', {})
        result = read(path)
        tokens += inf.get('eval_count', 0) + result.get('unobserved_output_token_upper_bound', 0)
        ns += sum(inf.get(k, 0) for k in ('eval_duration', 'prompt_eval_duration', 'load_duration'))
        if result.get('unobserved_model_calls'):
            ns += result['unobserved_model_calls'] * result['profile_config'].get('query_seconds', 180) * 1e9
    return {'output_tokens': tokens, 'inference_hours': ns / 3.6e12}


def run(args):
    batch = on_e(args.batch)
    batch.mkdir(parents=True, exist_ok=True)
    with Lock(batch / 'controller.lock'):
        if (batch / 'plan.json').exists():
            if not args.resume:
                raise ValueError('Existing batch requires --resume; plans cannot be changed')
            if args.profiles or args.tasks or args.seeds or args.manifest:
                raise ValueError('Resume takes no configuration overrides')
            plan = read(batch / 'plan.json')
        else:
            if not args.manifest or not args.profiles:
                raise ValueError('New batch needs manifest and profiles')
            args.seeds = args.seeds or [2108]
            plan = freeze(args, batch)
        pinned_vendor()
        for relative, checksum in plan['source_sha256'].items():
            if digest(batch / 'frozen-source' / relative) != checksum:
                raise RuntimeError('Frozen source corrupted')
        for image, expected in plan['images'].items():
            if json.loads(sandbox.docker('image', 'inspect', image).stdout)[0]['Id'] != expected['image_id']:
                raise RuntimeError('Image digest changed')
        count = 0
        for job in plan['jobs']:
            slot = batch / 'runs' / job['key']
            if (slot / 'complete.json').exists():
                continue
            budget = consumed()
            if budget['output_tokens'] >= 3000000 or budget['inference_hours'] >= 10:
                save(batch / 'budget-stop.json', budget)
                raise RuntimeError('Compute budget reached; partial evidence preserved')
            if api(11434, '/api/ps')['models']:
                raise RuntimeError('Foreign workload active; retry later')
            if next(t['digest'] for t in api(11435, '/api/tags')['models'] if t['name'] == MODEL) != plan['model_digest']:
                raise RuntimeError('Model digest changed')
            spec = plan['tasks'][job['task_id']]
            public, private = Path(spec['public']), Path(spec['private'])
            if {p.name: digest(p) for p in public.iterdir()} != spec['metadata']['public_sha256'] or digest(private) != spec['metadata']['private_row_sha256']:
                raise RuntimeError('Frozen task changed')
            slot.mkdir(parents=True, exist_ok=True)
            attempts = sorted(p for p in slot.glob('attempt-*') if p.is_dir())
            attempt = attempts[-1] if attempts else slot / 'attempt-01'
            if (attempt / 'result.json').exists() and read(attempt / 'result.json')['status'] == 'InfrastructureError':
                if not args.retry_infrastructure:
                    raise RuntimeError('Infrastructure attempt retained; resolve its cause and explicitly use --retry-infrastructure')
                save(attempt / 'retry-authorized.json', {'at': time.time(), 'reason': 'Explicit infrastructure retry; original result retained'})
                attempt = slot / ('attempt-' + str(len(attempts) + 1).zfill(2))
            if not (attempt / 'result.json').exists():
                if attempt.exists():
                    claim = attempt.with_suffix('.claim.json')
                    if claim.exists() and alive(read(claim)['pid']):
                        raise RuntimeError('Runtime child still alive')
                    if not args.retry_interrupted:
                        raise RuntimeError('Interrupted attempt preserved; use --retry-interrupted')
                    if (attempt / 'container.json').exists():
                        owned = read(attempt / 'container.json')
                        inspection = subprocess.run(['docker', 'inspect', owned['container_id']], capture_output=True, text=True)
                        if inspection.returncode == 0:
                            labels = json.loads(inspection.stdout)[0]['Config'].get('Labels', {})
                            if labels.get('csc2108.eval-v2.run') != owned['run_id']:
                                raise RuntimeError('Container ownership mismatch')
                            sandbox.docker('rm', '-f', owned['container_id'])
                    save(attempt / 'interrupted.json', {'noticed_unix': time.time(), 'reason': 'No completed runtime record'})
                    attempt = slot / ('attempt-' + str(len(attempts) + 1).zfill(2))
                source_root = batch / 'frozen-source'
                script = source_root / ('local_eval_v2/runtime.py' if job['profile'] == 'heredoc-v6-16k-common' else 'local_optimization/runtime_opt.py')
                invocation = [sys.executable, str(script), '--task', str(public), '--output', str(attempt), '--model', MODEL,
                              '--profile', job['profile'], '--seed', str(job['seed']), '--seconds', str(plan['seconds'])]
                with (slot / (attempt.name + '.stdout.txt')).open('w', encoding='utf-8') as stdout, (slot / (attempt.name + '.stderr.txt')).open('w', encoding='utf-8') as stderr:
                    invocation_started = time.monotonic()
                    child = subprocess.Popen(invocation, stdout=stdout, stderr=stderr)
                    save(attempt.with_suffix('.claim.json'), {'pid': child.pid, 'invocation': invocation, 'started': time.time()})
                    child.wait(timeout=plan['seconds'] + 150)
                save(attempt / 'invocation-timing.json', {'wall_seconds': time.monotonic() - invocation_started, 'includes': 'interpreter startup, preflight, model loading, agent, extraction, cleanup and telemetry; excludes judge'})
            result = read(attempt / 'result.json')
            if result.get('status') == 'InfrastructureError' or not result.get('sampler_wire_verified') or (not result.get('token_telemetry_complete') and result.get('status') != 'ModelTimeout'):
                raise RuntimeError('Runtime infrastructure/wire/telemetry failure; evidence retained: ' + str(attempt))
            wire = read(attempt / 'ollama-requests.json')
            if not wire or not all(r.get('think') is plan['profiles'][job['profile']]['thinking'] and r['model'] == MODEL for r in wire):
                raise RuntimeError('Thinking/model wire invariant failed')
            if plan['profiles'][job['profile']].get('native_history') == 'fixed' and not result.get('native_history_wire_verified'):
                raise RuntimeError('Native history invariant failed')
            if not (attempt / 'private_evaluation.json').exists():
                judge_attempt = attempt / ('judge-attempt-' + str(len(list(attempt.glob('judge-attempt-*'))) + 1).zfill(2))
                judge_attempt.mkdir()
                if (attempt / 'solution.py').exists():
                    shutil.copyfile(attempt / 'solution.py', judge_attempt / 'solution.py')
                judge_started = time.monotonic()
                evaluation = score(judge_attempt, private, VENDOR, JUDGE)
                save(judge_attempt / 'timing.json', {'wall_seconds': time.monotonic() - judge_started})
                save(judge_attempt / 'evaluation.json', evaluation)
                if evaluation['status'] == 'infrastructure_error':
                    raise RuntimeError('Judge infrastructure failure; isolated attempt retained')
                save(attempt / 'private_evaluation.json', evaluation)
            evaluation = read(attempt / 'private_evaluation.json')
            save(slot / 'complete.json', {'attempt': str(attempt), 'evaluation': evaluation['status'], 'finished': time.time()})
            count += 1
            save(batch / 'progress.json', {'completed': sum((batch / 'runs' / j['key'] / 'complete.json').exists() for j in plan['jobs']),
                 'planned': len(plan['jobs']), 'consumed': consumed(), 'last_job': job, 'last_evaluation': evaluation['status']})
            print(json.dumps({'task': job['task_id'], 'profile': job['profile'], 'seed': job['seed'], 'official': evaluation['status'], 'seconds': round(result['elapsed_seconds'], 2), 'tokens': result['inference']['eval_count']}), flush=True)
            if args.max_new and count >= args.max_new:
                break
        print(json.dumps({'completed_this_invocation': count, 'consumed': consumed()}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--batch', type=Path, required=True)
    p.add_argument('--manifest', type=Path)
    p.add_argument('--profiles', nargs='+')
    p.add_argument('--tasks', nargs='+')
    p.add_argument('--seeds', nargs='+', type=int)
    p.add_argument('--seconds', type=int, default=600)
    p.add_argument('--resume', action='store_true')
    p.add_argument('--retry-interrupted', action='store_true')
    p.add_argument('--retry-infrastructure', action='store_true', help='Preserve and retry a genuine infrastructure error; never retries resource timeouts')
    p.add_argument('--max-new', type=int)
    args = p.parse_args()
    if not 1 <= args.seconds <= 1200:
        p.error('Invalid wall budget')
    run(args)
