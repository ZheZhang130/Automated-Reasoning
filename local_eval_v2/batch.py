"""Frozen, sequential, resumable model/task/repetition evaluation; no private feedback to agents."""
import argparse
import json
import os
import socket
import subprocess
import sys
import time
import importlib.metadata
from pathlib import Path

from common import BASELINE, DATA, MODELS, ROOT, Lock, alive, digest, on_e, read, save
from dataset import EVALUATOR
from runtime import api, exclusive_gpu
import runner as v3
from pilot import score


def source_hashes():
    paths = [ROOT / p for p in ('runtime.py', 'common.py', 'profiles.json', 'public_check.py', 'batch.py', 'judge.Dockerfile', 'dataset.py')]
    paths += [BASELINE / p for p in ('runner.py', 'probe.py', 'judge_lcb.py', 'pilot.py', 'prepare_lcb.py', 'models.json', 'requirements.lock', 'judge-requirements.lock', 'env.ps1')]
    return {str(path.relative_to(ROOT.parent)): digest(path) for path in paths}


def schedule(manifest, models, repetitions, profile):
    jobs = []
    for index, task in enumerate(manifest['tasks']):
        for repetition in range(1, repetitions + 1):
            offset = (index * repetitions + repetition - 1) % len(models)
            ordered = models[offset:] + models[:offset]
            for model in ordered:
                key = task['task_id'] + '--' + model.replace(':', '_') + '--r' + str(repetition).zfill(2)
                jobs.append({'key': key, 'task_id': task['task_id'], 'model': model, 'profile': profile,
                             'repetition': repetition, 'seed': 2107 + repetition})
    return jobs


def freeze(args):
    manifest = read(args.manifest)
    if manifest['evaluator_revision'] != EVALUATOR:
        raise ValueError('Unsupported official evaluator revision')
    root = args.manifest.resolve().parent
    models = args.models or MODELS
    profile = args.profile or 'heredoc-v6-16k-common'
    repetitions = args.repetitions if args.repetitions is not None else 2
    if not 1 <= repetitions <= 20:
        raise ValueError('Invalid repetition count')
    tasks = {}
    for task in manifest['tasks']:
        import re
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*', task['task_id']) or task['task_id'] in tasks:
            raise ValueError('Invalid or duplicate task identity')
        public = root / 'public' / task['task_id']
        hashes = {p.name: digest(p) for p in public.iterdir()}
        if hashes != task['public_sha256']:
            raise ValueError('Public manifest hashes differ for ' + task['task_id'])
        private = root / 'evaluator_private' / (task['task_id'] + '.json')
        if not private.exists():
            private = root / 'private' / (task['task_id'] + '.json')
        tasks[task['task_id']] = {'public': str(public), 'private': str(private),
                                 'public_sha256': hashes, 'private_sha256': digest(private)}
    vendor = Path('E:/CSC2108Local/vendor/LiveCodeBench')
    revision = subprocess.run(['git', '-C', str(vendor), 'rev-parse', 'HEAD'], check=True, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(['git', '-C', str(vendor), 'status', '--porcelain'], check=True, capture_output=True, text=True).stdout
    if revision != EVALUATOR or dirty:
        raise RuntimeError('Official evaluator checkout must be clean and pinned')
    exclusive_gpu()
    images = {image: v3.isolation_preflight(image, Path('E:/DockerDesktop')) for image in (v3.IMAGE, 'csc2108-lcb-judge:v2')}
    tags = api(11435, '/api/tags')['models']
    plan = {'manifest': manifest, 'manifest_path': str(args.manifest.resolve()), 'tasks': tasks, 'models': models,
            'profile': profile, 'profile_config': read(ROOT / 'profiles.json')[profile],
            'repetitions': repetitions, 'actions': 20, 'repairs': 3, 'seconds': 600,
            'seed_policy': '2107 + repetition, same across all models and tasks',
            'source_sha256': source_hashes(), 'model_digests': {m: next(t['digest'] for t in tags if t['name'] == m) for m in models},
            'model_tags': tags, 'images': images, 'vendor': str(vendor), 'created': time.time(),
            'gpu': subprocess.run(['nvidia-smi', '--query-gpu=name,uuid,memory.total,driver_version', '--format=csv,noheader'], capture_output=True, text=True).stdout,
            'python': sys.version, 'git_base': subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
    plan['software'] = {'ollama_project': api(11435, '/api/version'), 'ollama_desktop': api(11434, '/api/version'),
                        'packages': dict(sorted((d.metadata['Name'], d.version) for d in importlib.metadata.distributions()))}
    plan['jobs'] = schedule(manifest, models, repetitions, profile)
    return plan


def run_batch(args):
    batch = on_e(args.batch)
    if (batch / 'plan.json').exists():
        if not args.resume:
            raise ValueError('Existing batch requires --resume')
        plan = read(batch / 'plan.json')
        for key in ('models', 'profile', 'repetitions'):
            value = getattr(args, key, None)
            if value is not None and value != plan[key]:
                raise ValueError('Cannot change a frozen batch: ' + key)
    else:
        if batch.exists() and any(batch.iterdir()):
            raise ValueError('New batch directory must be empty')
        if args.manifest is None:
            raise ValueError('--manifest required for a new batch')
        batch.mkdir(parents=True, exist_ok=True)
        plan = freeze(args)
        save(batch / 'plan.json', plan)
    with Lock(batch / 'batch.lock'):
        for relative, checksum in plan['source_sha256'].items():
            archived = batch / 'frozen-source' / relative
            if not archived.exists():
                source = ROOT.parent / relative
                if digest(source) != checksum:
                    raise RuntimeError('Cannot archive a changed frozen source: ' + relative)
                archived.parent.mkdir(parents=True, exist_ok=True)
                archived.write_bytes(source.read_bytes())
            if digest(archived) != checksum:
                raise RuntimeError('Frozen source archive changed: ' + relative)
        if plan.get('vendor'):
            revision = subprocess.run(['git', '-C', plan['vendor'], 'rev-parse', 'HEAD'], check=True, capture_output=True, text=True).stdout.strip()
            dirty = subprocess.run(['git', '-C', plan['vendor'], 'status', '--porcelain'], check=True, capture_output=True, text=True).stdout
            if revision != EVALUATOR or dirty:
                raise RuntimeError('Official evaluator checkout changed')
        for image, expected in plan.get('images', {}).items():
            actual = json.loads(v3.docker('image', 'inspect', image).stdout)[0]['Id']
            if actual != expected['image_id']:
                raise RuntimeError('Frozen image changed: ' + image)
        completed_now = 0
        for job in plan['jobs']:
            if plan['source_sha256'] != source_hashes():
                raise RuntimeError('Frozen implementation changed; use a new batch')
            slot = batch / 'runs' / job['key']
            if (slot / 'complete.json').exists():
                continue
            spec = plan['tasks'][job['task_id']]
            public, private = Path(spec['public']), Path(spec['private'])
            if {p.name: digest(p) for p in public.iterdir()} != spec['public_sha256'] or digest(private) != spec['private_sha256']:
                raise RuntimeError('Frozen task content changed')
            tags = api(11435, '/api/tags')['models']
            if next(t['digest'] for t in tags if t['name'] == job['model']) != plan['model_digests'][job['model']]:
                raise RuntimeError('Model digest changed')
            attempts = sorted(slot.glob('attempt-*')) if slot.exists() else []
            attempts = [p for p in attempts if p.is_dir()]
            attempt = attempts[-1] if attempts else slot / 'attempt-01'
            result_path = attempt / 'result.json'
            if not result_path.exists():
                claim = attempt.with_suffix('.claim.json')
                if claim.exists() and alive(read(claim).get('pid')):
                    raise RuntimeError('Previous runtime child is still active; resume after it exits')
                if attempt.exists():
                    save(attempt / 'interrupted.json', {'at': time.time(), 'reason': 'Runtime did not finish; trajectory preserved'})
                    if not args.retry_interrupted:
                        raise RuntimeError('Interrupted attempt requires explicit --retry-interrupted: ' + str(attempt))
                    if (attempt / 'container.json').exists():
                        owned = read(attempt / 'container.json')
                        inspection = subprocess.run(['docker', 'inspect', owned['container_id']], capture_output=True, text=True)
                        if inspection.returncode == 0:
                            labels = json.loads(inspection.stdout)[0]['Config'].get('Labels', {})
                            if labels.get('csc2108.eval-v2.run') != owned['run_id']:
                                raise RuntimeError('Container ownership differs; cleanup refused')
                            v3.docker('rm', '-f', owned['container_id'])
                    attempt = slot / ('attempt-' + str(len(attempts) + 1).zfill(2))
                    result_path = attempt / 'result.json'
                    claim = attempt.with_suffix('.claim.json')
                exclusive_gpu()
                slot.mkdir(parents=True, exist_ok=True)
                command = [sys.executable, str(ROOT / 'runtime.py'), '--task', str(public), '--output', str(attempt),
                           '--model', job['model'], '--profile', plan['profile'], '--seed', str(job['seed']),
                           '--actions', str(plan['actions']), '--repairs', str(plan['repairs']), '--seconds', str(plan['seconds'])]
                with attempt.with_suffix('.stdout.log').open('w', encoding='utf-8') as stdout, attempt.with_suffix('.stderr.log').open('w', encoding='utf-8') as stderr:
                    process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
                    save(claim, {'pid': process.pid, 'host': socket.gethostname(), 'command': command, 'started': time.time()})
                    try:
                        process.wait(timeout=plan['seconds'] + 120)
                    except (KeyboardInterrupt, subprocess.TimeoutExpired):
                        process.terminate()
                        process.wait(timeout=15)
                        save(slot / 'interrupted.json', {'attempt': str(attempt), 'time': time.time()})
                        raise
                if not result_path.exists():
                    raise RuntimeError('Runtime exited without a result; preserve logs and recover explicitly')
            result = read(result_path)
            if plan['profile_config'].get('sampler') and not result.get('sampler_wire_verified'):
                raise RuntimeError('Sampler request verification failed; preserve this attempt and investigate before judging')
            evaluation_path = attempt / 'private_evaluation.json'
            if evaluation_path.exists():
                evaluation = read(evaluation_path)
            else:
                evaluation = score(attempt, private, Path(plan['vendor']), 'csc2108-lcb-judge:v2')
                save(evaluation_path, evaluation)
            save(slot / 'complete.json', {'job': job, 'attempt': str(attempt), 'agent_status': result['status'],
                                          'official_status': evaluation['status'], 'completed': time.time()})
            completed_now += 1
            done = len(list((batch / 'runs').glob('*/complete.json')))
            save(batch / 'progress.json', {'planned': len(plan['jobs']), 'completed': done, 'last_job': job})
            print(json.dumps({'completed': done, 'planned': len(plan['jobs']), **job,
                              'agent_status': result['status'], 'official': evaluation['status'],
                              'seconds': result['elapsed_seconds']}), flush=True)
            if args.max_new_runs and completed_now >= args.max_new_runs:
                return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--profile')
    parser.add_argument('--models', nargs='+', choices=MODELS)
    parser.add_argument('--repetitions', type=int)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--retry-interrupted', action='store_true')
    parser.add_argument('--max-new-runs', type=int, default=0)
    run_batch(parser.parse_args())
