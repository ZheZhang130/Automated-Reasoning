"""One scheduled attempt (A/C/D) -> Peter's run-record handoff, plus hidden evaluation.

An attempt runs in its own child process under a hard outer timeout (see ``batch``), so a
hung model call or Docker command cannot outlive its budget. Hidden evaluation is a separate
command that never runs inside an agent process and whose results never reach any model.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from .common import (ACTIONS, CONDITIONS, MODEL, PROFILE, REPAIRS, REPO, SECONDS, SEED, append_jsonl, host_identity,
                     read_json, sha256_bytes, sha256_file, settings, study_root, utc_now, write_json)
from . import backend, guidance
from .tasks import load_statement

EXIT_STATUS = {'Submitted': 'submitted', 'ActionLimit': 'action_limit', 'LimitsExceeded': 'action_limit',
               'RepairLimit': 'repair_limit', 'Deadline': 'deadline', 'TimeExceeded': 'deadline',
               'RepeatedFormatError': 'agent_error', 'CommandExecutionError': 'agent_error',
               'InfrastructureError': 'infra_error'}


def exit_status(frozen):
    status = frozen.get('status')
    if status == 'InfrastructureError' and frozen.get('error_type'):
        # Exceptions escaping agent.run (for example a model request timeout) leave the frozen default.
        return 'infra_error'
    return EXIT_STATUS.get(status, 'agent_error')


def coding_usage(agent_dir):
    path = agent_dir / 'ollama-responses.json'
    if not path.exists():
        return []
    return [{'prompt_tokens': r.get('prompt_eval_count'), 'completion_tokens': r.get('eval_count'),
             'cost_usd': None, 'done_reason': r.get('done_reason'),
             'eval_seconds': (r.get('eval_duration') or 0) / 1e9} for r in read_json(path)]


def source_state():
    try:
        head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=REPO, capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(['git', 'status', '--porcelain', '--', 'guided_agent', 'local_eval_v2', 'local_baseline',
                                'local_agent', 'judge', 'planning_frontier', 'contract_frontier'],
                               cwd=REPO, capture_output=True, text=True).stdout.strip()
    except OSError:
        return {'commit': None, 'dirty': None}
    files = {p.name: sha256_file(p) for p in sorted((REPO / 'guided_agent').glob('*.py'))}
    return {'commit': head, 'dirty': bool(dirty), 'dirty_paths': dirty.splitlines()[:20], 'guided_agent_sha256': files}


def run_attempt(spec):
    host = settings(spec.get('backend', 'auto'))
    study = study_root(host, spec.get('study'))
    task_id, condition = spec['task_id'], spec['condition']
    kind = CONDITIONS[condition]
    out = Path(spec['output'])
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / 'spec.json', spec)
    started_utc = utc_now()
    statement = load_statement(study, task_id)
    record = {'run_id': spec['run_id'], 'task_id': task_id, 'condition': condition, 'repeat': spec.get('repeat', 1),
              'coding_model': MODEL, 'guidance_model': None, 'exit_status': 'infra_error', 'raw_exit_status': None,
              'submission_sha256': None, 'n_actions': 0, 'n_repairs': 0,
              'guidance': {'kind': kind, 'triggered': kind is not None, 'delivered': False, 'error': None},
              'usage': {'coding': [], 'guidance': []}, 'wall_seconds': None, 'host': host_identity()['node'],
              'backend': 'guided_agent/frozen-runtime', 'profile': PROFILE, 'seed': spec.get('seed', SEED),
              'budgets': {'actions': ACTIONS, 'repairs': REPAIRS, 'seconds': SECONDS, 'request_seconds': 180},
              'injection': spec.get('injection', 'inject-v1') if kind else None, 'aci': spec.get('aci') or {},
              'host_identity': host_identity(), 'host_backend': host.backend, 'started_utc': started_utc,
              'cohort': spec.get('cohort'), 'batch': spec.get('batch'), 'source': source_state()}
    guidance_text = template = None
    attempts = []
    started = time.monotonic()
    try:
        from local_agent.cli import verify
        record['frozen_verification'] = {k: v for k, v in verify(settings=host).items()
                                         if k in ('frozen_files_verified', 'model_digest', 'selection_sha256',
                                                  'system_prompt_sha256', 'packages', 'ollama', 'image_ids')}
        if kind:
            generated, raw = guidance.load_for_run(spec['guidance'], statement)
            if raw['kind'] != kind or raw['task_id'] != task_id:
                raise ValueError('Guidance artifact does not match this condition/task')
            guidance_text = generated['text']
            template = guidance.INJECTION[record['injection']][kind]
            record['guidance_model'] = raw['requested_model']
            record['guidance_provenance'] = {k: raw.get(k) for k in (
                'provider', 'label', 'prompt_id', 'requested_model', 'observed_model', 'reasoning_effort',
                'statement_sha256', 'system_prompt_sha256', 'latency_seconds', 'cost_usd', 'word_count',
                'soft_code_flags', 'created_utc')} | {'artifact': str(spec['guidance']),
                                                      'artifact_sha256': sha256_file(spec['guidance'])}
            usage = raw.get('usage') or {}
            record['usage']['guidance'] = [{'prompt_tokens': usage.get('prompt_tokens'),
                                            'completion_tokens': usage.get('completion_tokens'),
                                            'cost_usd': raw.get('cost_usd')}]
            record['frontier_generation_seconds'] = raw.get('latency_seconds')
        runtime = backend.frozen_runtime(host)
        base, adapter = backend.host_base_function(runtime, host)
        judge = backend.judge_client(study, 'public')
        info = judge.up()
        if task_id not in info.get('tasks', []):
            raise RuntimeError('judge-public does not hold this task')
        record['judge_public'] = {k: info.get(k) for k in ('judge_version', 'suite', 'tests_sha256', 'fingerprint')}
        record['judge_public']['image_id'] = judge._image_id()
        agent_cls, env_cls = backend.make_classes(runtime, guidance_text=guidance_text, template=template, judge=judge,
                                                  task_id=task_id, attempts=attempts, aci=spec.get('aci'))
        run = backend.bound_run(base, agent_cls, env_cls, backend.aci_globals(spec.get('aci')))
        record['host_adapter'] = adapter
        agent_dir = out / ('agent-' + spec['run_id'])
        from local_agent.platform_support import model_lock
        coding_started = time.monotonic()
        with model_lock(host):
            frozen = run(study / 'bundles' / task_id, agent_dir, MODEL, PROFILE, seed=record['seed'],
                         actions=ACTIONS, repairs=REPAIRS, seconds=SECONDS)
        record['local_coding_seconds'] = round(time.monotonic() - coding_started, 2)
        record['frozen_result'] = str(agent_dir / 'result.json')
        record['raw_exit_status'] = frozen.get('status')
        record['exit_status'] = exit_status(frozen)
        record['frozen_error'] = {k: frozen.get(k) for k in ('error_type', 'error') if frozen.get(k)}
        record['n_actions'], record['n_repairs'] = frozen.get('actions', 0), frozen.get('repairs', 0)
        record['guidance']['delivered'] = kind is not None and frozen.get('model_calls', 0) > 0
        record['usage']['coding'] = coding_usage(agent_dir)
        for key in ('format_errors', 'model_calls', 'token_telemetry_complete', 'sampler_wire_verified', 'inference',
                    'context_events', 'elapsed_seconds'):
            record[key] = frozen.get(key)
        record['model_identity'] = {k: (frozen.get('model_metadata') or {}).get(k) for k in ('details', 'modified_at')}
        record['model_digest'] = next((m.get('digest') for m in (frozen.get('tags') or {}).get('models', [])
                                       if m.get('name') == MODEL), None)
        record['agent_image'] = (frozen.get('isolation') or {}).get('image_id')
        record['gpu'] = {'before': frozen.get('gpu_before'), 'after': frozen.get('gpu_after')}
        solution = agent_dir / 'solution.py'
        if solution.exists():
            shutil.copyfile(solution, out / 'submission.py')
            record['submission_sha256'] = sha256_file(out / 'submission.py')
    except Exception as error:
        record['setup_error'] = f'{type(error).__name__}: {error}'
        if kind and not guidance_text:
            record['guidance']['error'] = record['setup_error']
    finally:
        record['wall_seconds'] = round(time.monotonic() - started, 2)
        record['finished_utc'] = utc_now()
        (out / 'attempts.jsonl').write_text(''.join(json.dumps(a) + '\n' for a in attempts), encoding='utf-8')
        record['public_attempts'] = len(attempts)
        write_json(out / 'result.json', record)
    return record


def run_child(spec, timeout):
    """Hard outer supervisor; on timeout only this attempt's labelled container is removed."""
    out = Path(spec['output'])
    spec_path = out.parent / (out.name + '.spec.json')
    write_json(spec_path, spec)
    command = [sys.executable, '-m', 'guided_agent', 'run-one', str(spec_path)]
    try:
        proc = subprocess.run(command, cwd=REPO, timeout=timeout, capture_output=True, text=True,
                              encoding='utf-8', errors='replace')
        (out.parent / (out.name + '.log')).write_text(proc.stdout[-20000:] + '\n--- stderr ---\n' + proc.stderr[-20000:],
                                                       encoding='utf-8')
    except subprocess.TimeoutExpired:
        label = 'csc2108.eval-v2.run=agent-' + spec['run_id']
        ids = subprocess.run(['docker', 'ps', '-aq', '--filter', 'label=' + label], capture_output=True, text=True).stdout.split()
        for container in ids:
            subprocess.run(['docker', 'rm', '-f', container], capture_output=True)
        record = read_json(out / 'result.json') if (out / 'result.json').exists() else {'run_id': spec['run_id']}
        record.update(exit_status='infra_error', raw_exit_status='OuterTimeout', outer_timeout_seconds=timeout,
                      removed_containers=ids)
        write_json(out / 'result.json', record)
    return read_json(out / 'result.json')


def evaluate(batch_dir, study):
    """Hidden scoring after all attempts finished. Writes <batch>/eval/<run_id>.json."""
    judge = backend.judge_client(study, 'hidden')
    info = judge.up()
    eval_dir = Path(batch_dir) / 'eval'
    eval_dir.mkdir(exist_ok=True)
    results = {}
    for result_path in sorted(Path(batch_dir).glob('*/result.json')):
        record = read_json(result_path)
        run_id = record['run_id']
        if (eval_dir / f'{run_id}.json').exists():
            results[run_id] = read_json(eval_dir / f'{run_id}.json')
            continue
        submission = result_path.parent / 'submission.py'
        if record.get('submission_sha256') is None or not submission.exists():
            outcome = {'status': 'missing_submission', 'verdict': 'MISSING'}
        else:
            code = submission.read_bytes()
            if sha256_bytes(code) != record['submission_sha256']:
                outcome = {'status': 'infrastructure_error', 'error': 'submission hash mismatch'}
            else:
                result = judge.run(record['task_id'], code)
                outcome = {k: result.get(k) for k in ('status', 'passed', 'total', 'verdict_counts', 'judge_version',
                                                       'tests_sha256', 'code_sha256', 'error')}
        outcome |= {'run_id': run_id, 'task_id': record['task_id'], 'condition': record['condition'],
                    'suite': 'hidden', 'judge_tests_sha256': info.get('tests_sha256'), 'evaluated_utc': utc_now()}
        write_json(eval_dir / f'{run_id}.json', outcome)
        results[run_id] = outcome
    return results
