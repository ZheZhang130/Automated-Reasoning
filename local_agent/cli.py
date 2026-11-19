"""Run public bundles and judge candidates in separate, isolated invocations."""
import argparse
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = Path('E:/CSC2108Local')
ENDPOINT = 'http://127.0.0.1:11435'
PROFILE = 'heredoc-v6-16k-common'
MODEL = 'qwen3.5:9b'
VENDOR = ROOT / 'vendor/LiveCodeBench'
EVALUATOR_REVISION = '28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24'
PACKAGES = {'mini-swe-agent': '2.4.6', 'litellm': '1.81.16',
            'pydantic': '2.12.5', 'pydantic_core': '2.41.5', 'numpy': '2.4.6'}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, indent=2, default=str) + '\n', encoding='utf-8')
    os.replace(temp, path)


def fresh_output(path):
    path = Path(path).resolve()
    if path.drive.upper() != 'E:' or path.is_relative_to(REPO):
        raise ValueError('Runtime artifacts must be outside the checkout on E:')
    path.mkdir(parents=True, exist_ok=False)
    return path


def verify(*, services=True, evaluator=False):
    """Fail before inference when identity differs; never rewrite frozen files."""
    selection_path = REPO / 'local_optimization/final_selection.json'
    selection = read(selection_path)
    recommendation = read(REPO / 'local_optimization/final_recommendation.json')
    if recommendation['selection_sha256'] != digest(selection_path):
        raise RuntimeError('Recommendation/selection hash mismatch')
    if recommendation['recommended_profile'] != PROFILE or recommendation['challenger_promoted']:
        raise RuntimeError('Original control is required')
    for name, expected in selection['runtime_sha256'].items():
        if digest(REPO / name) != expected:
            raise RuntimeError('Frozen source changed: ' + name)
    configuration = selection['frozen_configurations'][PROFILE]
    for name in ('local_optimization/profiles.json', 'local_eval_v2/profiles.json'):
        if read(REPO / name)[PROFILE] != configuration:
            raise RuntimeError('Frozen control changed: ' + name)
    versions = {p: importlib.metadata.version(p) for p in PACKAGES}
    if versions != PACKAGES or sys.version_info[:3] != (3, 11, 9):
        raise RuntimeError('Use the recorded Python 3.11.9 environment and package pins')
    result = {'profile': PROFILE, 'model': MODEL, 'model_digest': selection['model_digest'],
              'configuration': configuration, 'frozen_files_verified': len(selection['runtime_sha256']),
              'packages': versions, 'python': sys.version, 'endpoint': ENDPOINT,
              'budgets': {'actions': 20, 'repair_groups': 3, 'task_seconds': 600, 'request_seconds': 180},
              'selection_sha256': digest(selection_path),
              'image_ids': {name: item['image_id'] for name, item in selection['images'].items()},
              'system_prompt_sha256': prompt_hash(), 'services_checked': services}
    if services:
        import requests
        for image, metadata in selection['images'].items():
            actual = subprocess.check_output(['docker', 'image', 'inspect', image, '--format', '{{.Id}}'], text=True).strip()
            if actual != metadata['image_id']:
                raise RuntimeError('Frozen Docker image changed: ' + image)
        tags = requests.get(ENDPOINT + '/api/tags', timeout=10)
        tags.raise_for_status()
        model = next((m for m in tags.json()['models'] if m['name'] == MODEL), None)
        if not model or model['digest'] != selection['model_digest'] or model['details']['quantization_level'] != 'Q4_K_M':
            raise RuntimeError('Frozen Qwen model missing or changed; no automatic downloads')
        result['model_identity'] = model
        version = requests.get(ENDPOINT + '/api/version', timeout=10)
        version.raise_for_status()
        result['ollama'] = version.json()
    if evaluator:
        revision = subprocess.check_output(['git', '-C', str(VENDOR), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['git', '-C', str(VENDOR), 'status', '--porcelain'], text=True).strip()
        if revision != EVALUATOR_REVISION or dirty:
            raise RuntimeError('Independent evaluator checkout must be clean at the frozen revision')
        result['evaluator_revision'] = revision
    return result


def prompt_hash():
    # Parse the string without importing the runtime or altering module globals.
    import ast
    tree = ast.parse((REPO / 'local_eval_v2/runtime.py').read_text(encoding='utf-8'))
    prompt = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == 'PROMPT' for t in n.targets))
    return hashlib.sha256(prompt.encode('utf-8')).hexdigest()


def envelope(output, metadata, process, started):
    runtime_dir = output / 'runtime'
    record_path = runtime_dir / 'result.json'
    record = read(record_path) if record_path.is_file() else {}
    candidate = runtime_dir / 'solution.py'
    trajectory = runtime_dir / 'trajectory.json'
    captured = record.get('inference', {}).get('calls_captured', 0)
    missing = max(0, record.get('model_calls', 0) - captured)
    return {'schema_version': 1, 'run_id': output.name, 'status': record.get('status', 'InfrastructureError'),
            'candidate_path': str(candidate) if candidate.is_file() else None,
            'trajectory_path': str(trajectory) if trajectory.is_file() else None,
            'metadata_path': str(output / 'metadata.json'),
            'runtime_result_path': str(record_path) if record_path.is_file() else None,
            'output_path': str(output), 'process_returncode': process.returncode,
            'task_id': record.get('task_id'), 'termination_reason': record.get('status', 'InfrastructureError'),
            'timings': {'invocation_wall_seconds': time.monotonic() - started,
                        'agent_elapsed_seconds': record.get('elapsed_seconds'),
                        **{k + '_seconds': record.get('inference', {}).get(k, 0) / 1e9
                           for k in ('eval_duration', 'prompt_eval_duration', 'load_duration')}},
            'usage': {'observed_generated_tokens': record.get('inference', {}).get('eval_count', 0),
                      'unobserved_generated_tokens_upper_bound': missing * 4096,
                      'token_telemetry_complete': record.get('token_telemetry_complete', False),
                      'model_calls': record.get('model_calls', 0), 'actions': record.get('actions', 0),
                      'repair_groups': record.get('repairs', 0)},
            'model': metadata['model'], 'profile': metadata['profile'],
            'error': record.get('error')}


def run_task(args):
    task = args.task.resolve(strict=True)
    # The unchanged child validates the complete allowlist/schema and performs isolation preflight.
    metadata = verify()
    output = fresh_output(args.output)
    metadata.update(seed=args.seed, task_path=str(task), checkout=str(REPO),
                    checkout_commit=subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip(),
                    entrypoint_sha256=digest(__file__))
    save(output / 'metadata.json', metadata)
    command = [sys.executable, str(REPO / 'local_optimization/selected.py'),
               '--task', str(task), '--output', str(output / 'runtime'), '--seed', str(args.seed)]
    save(output / 'invocation.json', {'arguments': command, 'started_unix': time.time()})
    started = time.monotonic()
    # selected.py retains all original checks and invokes the original locked CLI.
    # Timeout/command/cleanup behavior stays owned by that frozen runtime.
    with (output / 'stdout.log').open('w', encoding='utf-8') as stdout, (output / 'stderr.log').open('w', encoding='utf-8') as stderr:
        process = subprocess.run(command, stdout=stdout, stderr=stderr)
    result = envelope(output, metadata, process, started)
    save(output / 'result.json', result)
    print(json.dumps(result), flush=True)
    return 2 if process.returncode or result['status'] == 'InfrastructureError' else 0


def evaluate(args):
    # A distinct command with no model call, no runtime resumption, no feedback channel.
    verify(evaluator=True)
    run = args.run.resolve(strict=True)
    result = read(run / 'result.json')
    source = Path(result['candidate_path']) if result.get('candidate_path') else None
    output = fresh_output(args.output)
    started = time.monotonic()
    if source is None or not source.is_file():
        evaluation = {'status': 'missing_submission'}
    else:
        runtime_record = read(result['runtime_result_path'])
        if digest(source) != runtime_record['submission_sha256']:
            raise RuntimeError('Candidate no longer matches the extracted source hash')
        # Copy bytes for the independent judge; never import or execute candidate on Windows.
        (output / 'solution.py').write_bytes(source.read_bytes())
        sys.path.insert(0, str(REPO / 'local_optimization'))
        from judge_watch import score
        evaluation = score(output, args.private_row.resolve(strict=True), VENDOR, 'csc2108-lcb-judge:v2')
    save(output / 'evaluation.json', evaluation)
    summary = {'status': evaluation['status'], 'evaluation_path': str(output / 'evaluation.json'),
               'judge_wall_seconds': time.monotonic() - started, 'run_path': str(run),
               'candidate_sha256': digest(source) if source and source.is_file() else None}
    save(output / 'result.json', summary)
    print(json.dumps(summary), flush=True)
    return 2 if evaluation['status'] == 'infrastructure_error' else 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest='command', required=True)
    run = commands.add_parser('run', help='Run one trusted public bundle; never accepts private tests')
    run.add_argument('--task', type=Path, required=True)
    run.add_argument('--output', type=Path, required=True)
    run.add_argument('--seed', type=int, default=2108)
    judge = commands.add_parser('evaluate', help='Independently judge an already completed run')
    judge.add_argument('--run', type=Path, required=True)
    judge.add_argument('--private-row', type=Path, required=True)
    judge.add_argument('--output', type=Path, required=True)
    check = commands.add_parser('verify', help='Check source/environment identity without inference')
    check.add_argument('--offline', action='store_true', help='Skip Docker and Ollama service checks')
    args = p.parse_args()
    if args.command == 'run':
        return run_task(args)
    if args.command == 'evaluate':
        return evaluate(args)
    print(json.dumps(verify(services=not args.offline), default=str), flush=True)
    return 0
