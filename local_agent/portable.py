"""Portable infrastructure around the unchanged original agent and official judge."""
import importlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import types
from pathlib import Path

from .platform_support import REPO, Settings, model_lock

BASE_IMAGE = 'python:3.11-slim-bookworm@sha256:a83ba18aef0f865b1a4a611c2cf460fe446f2795673bbb9fe43be570439e3b39'
JUDGE_IMAGE = 'csc2108-lcb-judge:portable-v1'


def recipe_hash():
    import hashlib
    return hashlib.sha256((REPO / 'local_agent/portable.Dockerfile').read_bytes()
                          + (REPO / 'local_agent/portable.Dockerfile.dockerignore').read_bytes()
                          + (REPO / 'local_baseline/judge-requirements.lock').read_bytes()
                          + BASE_IMAGE.encode()).hexdigest()


def inspect_image(image):
    return json.loads(subprocess.check_output(['docker', 'image', 'inspect', image], text=True))[0]


def docker_preflight(image):
    info = json.loads(subprocess.check_output(['docker', 'info', '--format', '{{json .}}'], text=True))
    if info.get('OSType') != 'linux' or not info.get('MemoryLimit') or not info.get('PidsLimit'):
        raise RuntimeError('A Linux Docker daemon supporting memory/PID limits is required')
    item = inspect_image(image)
    native = {'x86_64': 'amd64', 'aarch64': 'arm64'}.get(info.get('Architecture'), info.get('Architecture'))
    if item.get('Os') != 'linux' or item.get('Architecture') != native:
        raise RuntimeError('A native-architecture Linux agent image is required')
    return {'docker': {k: info.get(k) for k in ('ServerVersion', 'OSType', 'Architecture')},
            'image_id': item['Id'], 'image_architecture': item.get('Architecture'),
            'image_digests': item.get('RepoDigests'), 'storage_policy': 'managed by host Docker; no Windows WSL disk requirement'}


def verify_images(settings):
    from .cli import read
    if not settings.manifest.is_file():
        raise RuntimeError('Portable images are not provisioned; run python -m local_agent prepare')
    manifest = read(settings.manifest)
    if manifest.get('schema_version') != 1 or manifest['recipe_sha256'] != recipe_hash() or manifest['agent_reference'] != BASE_IMAGE:
        raise RuntimeError('Portable image recipe changed; explicitly provision images again')
    for role in ('agent', 'judge'):
        item = manifest[role]
        actual = inspect_image(item['reference'])
        if actual['Id'] != item['image_id'] or actual.get('Architecture') != item['architecture']:
            raise RuntimeError('Portable image changed: ' + role)
    if manifest['agent']['architecture'] != manifest['judge']['architecture']:
        raise RuntimeError('Agent and judge must use the same native architecture')
    docker_preflight(manifest['agent']['reference'])
    return manifest


def prepare(settings):
    """Explicit infrastructure provisioning only: never downloads or generates a model."""
    from .cli import EVALUATOR_REVISION, save, verify
    verify(services=False, settings=settings)
    settings.initialize()
    if settings.manifest.exists():
        raise RuntimeError('Image manifest already exists; preserve it before explicitly reprovisioning')
    try:
        inspect_image(BASE_IMAGE)
    except subprocess.CalledProcessError:
        subprocess.run(['docker', 'pull', BASE_IMAGE], check=True)
    docker_preflight(BASE_IMAGE)
    if not settings.vendor.exists():
        settings.vendor.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', 'clone', 'https://github.com/LiveCodeBench/LiveCodeBench.git', str(settings.vendor)], check=True)
        subprocess.run(['git', '-C', str(settings.vendor), 'checkout', '--detach', EVALUATOR_REVISION], check=True)
    # Do not change an existing vendor checkout, including a teammate's edits.
    verify(services=False, evaluator=True, settings=settings)
    command = ['docker', 'build', '-f', str(REPO / 'local_agent/portable.Dockerfile'), '-t', JUDGE_IMAGE]
    if os.environ.get('CSC2108_CA_BUNDLE'):
        ca = Path(os.environ['CSC2108_CA_BUNDLE']).expanduser().resolve(strict=True)
        command += ['--secret', 'id=ca,src=' + str(ca)]
    subprocess.run(command + [str(REPO)], check=True)
    manifest = {'schema_version': 1, 'recipe_sha256': recipe_hash(), 'agent_reference': BASE_IMAGE,
                'host': platform.platform(), 'agent': {}, 'judge': {}}
    for role, reference in (('agent', BASE_IMAGE), ('judge', JUDGE_IMAGE)):
        item = inspect_image(reference)
        manifest[role] = {'reference': reference, 'image_id': item['Id'], 'architecture': item['Architecture']}
    save(settings.manifest, manifest)
    return {'status': 'prepared', 'manifest_path': str(settings.manifest), 'vendor': str(settings.vendor),
            'note': 'No model was downloaded. Run verify after starting your dedicated Ollama server.'}


def api(endpoint, route, payload=None):
    import requests
    response = requests.get(endpoint + route, timeout=15) if payload is None else requests.post(endpoint + route, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def exclusive(settings):
    import requests
    try:
        desktop = api('http://127.0.0.1:11434', '/api/ps')
    except requests.ConnectionError:
        desktop = {'models': []}  # A desktop app is optional on the portable host.
    if desktop['models']:
        raise RuntimeError('ForeignModelLoaded: leave Desktop models idle')
    approved = {'qwen3.5:9b', 'qwen2.5-coder:14b', 'qwen2.5-coder:7b'}
    for item in api(settings.endpoint, '/api/ps')['models']:
        if item['name'] not in approved:
            raise RuntimeError('Unexpected workload on the dedicated project endpoint')
        api(settings.endpoint, '/api/generate', {'model': item['name'], 'keep_alive': 0, 'stream': False})
    deadline = time.monotonic() + 20
    while api(settings.endpoint, '/api/ps')['models']:
        if time.monotonic() >= deadline:
            raise RuntimeError('Project model did not unload')
        time.sleep(.2)


def load_runtime(settings):
    settings.initialize()
    sys.path.insert(0, str(REPO / 'local_eval_v2'))
    return importlib.import_module('runtime')


def adapted_run(runtime, settings, manifest):
    """Copy only the function's host bindings; preserve original bytecode/classes/prompts."""
    def host_path(value, *parts):
        text = str(value).replace('\\', '/')
        if isinstance(value, str) and text == 'E:/CSC2108Local/logs/ollama-project.stderr.log':
            return settings.root.joinpath('logs/ollama-project.stderr.log', *parts)
        return Path(value, *parts)

    def host_run(command, **kwargs):
        if command[0] == 'nvidia-smi' and not shutil.which('nvidia-smi'):
            return subprocess.CompletedProcess(command, 0, stdout='unavailable: use Ollama size_vram/processor telemetry', stderr='')
        return subprocess.run(command, **kwargs)

    original = runtime.run
    bindings = original.__globals__ | {
        'Path': host_path, 'on_e': lambda path: settings.output(path, create=False),
        'ENDPOINT': settings.endpoint, 'exclusive_gpu': lambda: exclusive(settings),
        'api': lambda port, route, payload=None, timeout=15: api(settings.endpoint, route, payload),
        'subprocess': types.SimpleNamespace(run=host_run),
        'v3': types.SimpleNamespace(Budget=runtime.v3.Budget, IMAGE=manifest['agent']['reference'],
             container_args=runtime.v3.container_args, docker=runtime.v3.docker,
             isolation_preflight=lambda image, disk: docker_preflight(image))}
    function = types.FunctionType(original.__code__, bindings, original.__name__, original.__defaults__, original.__closure__)
    function.__kwdefaults__ = original.__kwdefaults__
    return function


def worker(task, output, seed, settings):
    from .cli import MODEL, PROFILE, save, verify
    verify(settings=settings)
    manifest = verify_images(settings)
    runtime = load_runtime(settings)
    log = settings.root / 'logs/ollama-project.stderr.log'
    log_available = log.exists()
    # An external foreground Ollama may not write our log; make that omission explicit.
    log.touch(exist_ok=True)
    with model_lock(settings):
        result = adapted_run(runtime, settings, manifest)(task, output, MODEL, PROFILE, seed=seed, actions=20, repairs=3, seconds=600)
    result['host_adapter'] = {'backend': 'portable', 'system': platform.system(), 'machine': platform.machine(),
                              'data_root': str(settings.root), 'ollama_endpoint': settings.endpoint,
                              'server_log_existed': log_available, 'images': manifest,
                              'note': 'Platform host adaptation; not a replication on the original Windows hardware.'}
    save(output / 'result.json', result)
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=2108)
    args = parser.parse_args()
    result = worker(args.task, args.output, args.seed, Settings.load('portable'))
    print(json.dumps({'status': result['status']}))
    raise SystemExit(2 if result['status'] == 'InfrastructureError' else 0)
