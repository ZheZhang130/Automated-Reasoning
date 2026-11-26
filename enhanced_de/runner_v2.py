"""Enhanced D-v2 and E-v2 attempt runner reusing frozen mini-SWE-agent bytecode unchanged.

Strictly preserves all 38 frozen files (`local_agent.cli.verify()` runs on every
attempt) and keeps all experimental runs inside a separate study root outside
the git checkout. Rebinds ONLY Agent and Environment globals via
`guided_agent.backend.bound_run`.
"""
import contextlib
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from minisweagent.exceptions import FormatError

from guided_agent import backend, measurement
from guided_agent.common import (
    ACTIONS,
    MODEL,
    PROFILE,
    REPAIRS,
    REPO,
    SECONDS,
    SEED,
    host_identity,
    read_json,
    sha256_bytes,
    sha256_file,
    settings,
    study_root,
    utc_now,
    write_json,
)
from guided_agent.runner import coding_usage, exit_status, source_state
from guided_agent.tasks import load_statement


def load_public_cases(study, task_id):
    p = Path(study) / 'bundles' / task_id / 'public_tests.json'
    return read_json(p) if p.is_file() else []


def make_enhanced_classes(
    runtime,
    *,
    judge,
    task_id,
    attempts,
    public_cases=None,
    guidance_text=None,
    template=None,
    d2_gate=None,
    e2_controller=None,
):
    """Build GuidedAgent & JudgedEnvironment subclasses with D2 gate and E2 hooks.

    Key invariants:
    - When d2_gate is None and e2_controller is None and guidance_text is None,
      behavior is byte-identical to Condition A (`frozen-v6`).
    - E2Stall hooks `FormatError` in `step()`, re-raises untouched so stock
      `n_consecutive_format_errors` increments identically, then delivers at the
      start of `query()` before calling `super().query()`.
    - D2Gate runs ONLY inside its own separate throwaway Docker container
      (never inside the agent's container, never on host) after a public pass,
      leaving the authoritative judge-public returncode unchanged.
    """
    v3 = runtime.v3
    public_cases = public_cases or []

    class EnhancedAgent(runtime.Agent):
        def __init__(self, *args, instance_template, **kwargs):
            if guidance_text is not None and template is not None:
                instance_template = template
            super().__init__(*args, instance_template=instance_template, **kwargs)
            self.instance_template_used = instance_template

        def run(self, task='', **kwargs):
            if guidance_text is not None:
                kwargs = kwargs | {'guide': guidance_text}
            return super().run(task, **kwargs)

        def step(self):
            try:
                return super().step()
            except FormatError:
                if e2_controller is not None:
                    raw_resp = None
                    capture = getattr(self.model, 'capture', None)
                    if capture is not None and getattr(capture, 'responses', None):
                        raw_resp = capture.responses[-1]
                    done_reason = (raw_resp or {}).get('done_reason')
                    raw_content = ((raw_resp or {}).get('message') or {}).get('content') or ''
                    try:
                        snap = self.env.snapshot()
                        has_cand = bool(snap and snap.strip())
                    except Exception:
                        has_cand = False
                    e2_controller.on_format_error(
                        done_reason=done_reason,
                        raw_content=raw_content,
                        consecutive_errors=self.n_consecutive_format_errors + 1,
                        has_candidate=has_cand,
                        budget=self.env.budget,
                        deadline=self.env.deadline,
                    )
                raise

        def query(self):
            if e2_controller is not None and e2_controller.pending is not None:
                # Deliver format-error / stall diagnosis right after stock loop appended rejection
                e2_controller.deliver(self)
            return super().query()

        def execute_actions(self, message):
            observations = super().execute_actions(message)
            if e2_controller is not None and e2_controller.pending is not None:
                # Deliver public-failure or public-pass review diagnosis in the SAME session
                observations = observations + (e2_controller.deliver(self) or [])
            return observations

    class EnhancedEnvironment(runtime.Environment):
        def __init__(self, *args, **kwargs):
            extra_s = 0
            if e2_controller is not None:
                extra_s += int(getattr(e2_controller, 'max_wait_seconds', 300)) + 30
            if d2_gate is not None:
                extra_s += 120
            if extra_s and isinstance(kwargs.get('container_timeout'), str):
                seconds = int(kwargs['container_timeout'].rstrip('s'))
                kwargs['container_timeout'] = f'{seconds + extra_s}s'
            super().__init__(*args, **kwargs)

        def execute(self, action, cwd='', *, timeout=None):
            command = action.get('command', '')
            if isinstance(command, str) and runtime.TEST_PATTERN.fullmatch(command):
                return self._public_judge(command)
            return super().execute(action, cwd, timeout=timeout)

        def _public_judge(self, command):
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise v3.limits('Deadline')
            self.budget.before()
            source = self.snapshot()
            started = time.monotonic()
            digest = hashlib.sha256(source).hexdigest() if source is not None else None
            result = judge.run(task_id, source or b'', timeout=max(10.0, min(120.0, remaining)))
            attempts.append({
                'seq': len(attempts) + 1,
                'time': utc_now(),
                'result': result,
                'delivered': True,
                'action': self.budget.actions,
                'source_sha256': digest,
            })
            self.last_candidate = source
            if (result.get('status') == 'infrastructure_error'
                    or result.get('task_id') != task_id
                    or result.get('suite') != 'public'):
                attempts[-1]['delivered'] = False
                self.evidence.append({
                    'command': command,
                    'action': self.budget.actions,
                    'source_sha256': digest,
                    'judge_infrastructure_error': result.get('error') or result.get('status'),
                })
                if e2_controller is not None:
                    e2_controller.observe_infrastructure_error(
                        action=self.budget.actions,
                        error=result.get('error') or result.get('status'),
                    )
                raise v3.limits('InfrastructureError')

            returncode = 0 if result['status'] == 'pass' else 1
            report_text = result.get('report', '')
            extra_notes = []
            gate_entry = None

            # D2 Gate (runs in separate throwaway Docker container on public pass only!)
            if d2_gate is not None and result['status'] == 'pass' and source and source.strip():
                gate_entry, gate_text = d2_gate.on_public_pass(source, digest)
                if gate_text:
                    extra_notes.append(gate_text)

            # E2 post-diagnosis non-blocking advisory V-check (only after diagnosis delivered)
            if e2_controller is not None and source and source.strip():
                adv = e2_controller.post_public_advisory(source, digest, result['status'])
                if adv:
                    extra_notes.append(adv)

            rendered_output = report_text
            if extra_notes:
                rendered_output = (report_text.rstrip() + '\n\n' + '\n\n'.join(extra_notes) + '\n')

            output = {'output': rendered_output, 'returncode': returncode, 'exception_info': ''}
            ev_rec = {
                'command': command,
                'action': self.budget.actions,
                'elapsed_seconds': time.monotonic() - started,
                'source_sha256': digest,
                'recognized_public_test': True,
                'public_status': result['status'],
                'judge': {k: result.get(k) for k in (
                    'status', 'passed', 'total', 'verdict_counts',
                    'code_sha256', 'tests_sha256', 'judge_version',
                )},
                **output,
            }
            if gate_entry is not None:
                ev_rec['d2_gate'] = gate_entry
            self.evidence.append(ev_rec)
            self.budget.tested(digest, returncode)

            if e2_controller is not None:
                e2_controller.on_public_result(
                    result=result,
                    source=source,
                    digest=digest,
                    budget=self.budget,
                    deadline=self.deadline,
                    public_cases=public_cases,
                )
            return output

    return EnhancedAgent, EnhancedEnvironment


def _build_controllers(spec, study, out, statement, task_id):
    """Instantiate D2GateChecker and/or E2 controller from spec."""
    d2_gate = None
    e2_ctrl = None
    d2_spec = spec.get('d2')
    e2_spec = spec.get('e2')

    if d2_spec:
        from . import d2_contract
        bank = read_json(d2_spec['bank_path'])
        if bank.get('task_id') != task_id:
            raise ValueError(f"D2 bank task_id {bank.get('task_id')} != {task_id}")
        if bank.get('statement_sha256') and bank['statement_sha256'] != hashlib.sha256(statement.encode('utf-8')).hexdigest():
            raise ValueError(f'D2 bank statement_sha256 mismatch for {task_id}')
        d2_gate = d2_contract.D2GateChecker(
            bank,
            mode=d2_spec.get('mode', 'oracle'),
            trigger=d2_spec.get('trigger', 'public_pass_only'),
            small_timeout=d2_spec.get('small_timeout', 2.0),
            stress_timeout=d2_spec.get('stress_timeout', 4.0),
        )

    if e2_spec:
        from . import e2_diagnosis
        kind = e2_spec['kind']
        provider_spec = e2_spec.get('provider_spec') or {'provider': 'codex'}
        provider = e2_diagnosis.make_e2_provider(provider_spec, study)
        max_wait = e2_spec.get('timeout', 300)
        if kind == 'strict':
            e2_ctrl = e2_diagnosis.E2StrictController(
                provider=provider,
                statement=statement,
                task_id=task_id,
                out_dir=out / 'e2_diagnosis',
                enable_advisory_vchecks=e2_spec.get('enable_advisory_vchecks', True),
                max_wait_seconds=max_wait,
            )
        elif kind == 'stall':
            e2_ctrl = e2_diagnosis.E2StallController(
                provider=provider,
                statement=statement,
                task_id=task_id,
                out_dir=out / 'e2_diagnosis',
                mode=e2_spec.get('mode', 'stall-diag'),
                plan_path=e2_spec.get('plan_path'),
                enable_public_fallback=e2_spec.get('enable_public_fallback', False),
                max_wait_seconds=max_wait,
            )
        elif kind == 'review':
            e2_ctrl = e2_diagnosis.E2ReviewController(
                provider=provider,
                statement=statement,
                task_id=task_id,
                out_dir=out / 'e2_diagnosis',
                max_wait_seconds=max_wait,
            )
        else:
            raise ValueError(f'Unknown e2 kind: {kind!r}')
    return d2_gate, e2_ctrl


def run_enhanced_attempt(spec):
    """Run one enhanced_de attempt (A, D2-*, E2-*) with frozen runtime verification."""
    host = settings(spec.get('backend', 'auto'))
    study = study_root(host, spec.get('study'))
    task_id = spec['task_id']
    arm = spec['arm']  # e.g. 'A', 'D2-oracle', 'D2-inputs-stress', 'E2-strict', 'E2-stall', 'E2-stall-clate', 'E2-stall-neutral', 'E2-review'
    condition = spec.get('condition', 'A')
    out = Path(spec['output'])
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / 'spec.json', spec)
    started_utc = utc_now()
    statement = load_statement(study, task_id)
    public_cases = load_public_cases(study, task_id)

    record = {
        'run_id': spec['run_id'],
        'task_id': task_id,
        'condition': condition,
        'arm': arm,
        'repeat': spec.get('repeat', 1),
        'coding_model': MODEL,
        'guidance_model': None,
        'exit_status': 'infra_error',
        'raw_exit_status': None,
        'submission_sha256': None,
        'n_actions': 0,
        'n_repairs': 0,
        'guidance': {'kind': arm, 'triggered': False, 'delivered': False, 'error': None},
        'usage': {'coding': [], 'guidance': []},
        'wall_seconds': None,
        'host': host_identity()['node'],
        'backend': 'enhanced_de/frozen-runtime',
        'profile': PROFILE,
        'seed': spec.get('seed', SEED),
        'budgets': {'actions': ACTIONS, 'repairs': REPAIRS, 'seconds': SECONDS, 'request_seconds': 180},
        'host_identity': host_identity(),
        'host_backend': host.backend,
        'started_utc': started_utc,
        'cohort': spec.get('cohort'),
        'batch': spec.get('batch'),
        'source': source_state(),
    }
    attempts = []
    d2_gate = e2_ctrl = None
    started = time.monotonic()
    try:
        from local_agent.cli import verify
        record['frozen_verification'] = {
            k: v for k, v in verify(settings=host).items()
            if k in ('frozen_files_verified', 'model_digest', 'selection_sha256',
                     'system_prompt_sha256', 'packages', 'ollama', 'image_ids')
        }
        d2_gate, e2_ctrl = _build_controllers(spec, study, out, statement, task_id)
        runtime = backend.frozen_runtime(host)
        base, adapter = backend.host_base_function(runtime, host)
        judge = backend.judge_client(study, 'public')
        info = judge.up()
        if task_id not in info.get('tasks', []):
            raise RuntimeError(f'judge-public does not hold {task_id}')
        record['judge_public'] = {k: info.get(k) for k in ('judge_version', 'suite', 'tests_sha256', 'fingerprint')}
        record['judge_public']['image_id'] = judge._image_id()

        agent_cls, env_cls = make_enhanced_classes(
            runtime,
            judge=judge,
            task_id=task_id,
            attempts=attempts,
            public_cases=public_cases,
            d2_gate=d2_gate,
            e2_controller=e2_ctrl,
        )
        run = backend.bound_run(base, agent_cls, env_cls, {})
        record['host_adapter'] = adapter
        agent_dir = out / ('agent-' + spec['run_id'])
        from local_agent.platform_support import model_lock

        budgets = {'actions': ACTIONS, 'repairs': REPAIRS, 'seconds': SECONDS}
        coding_started = time.monotonic()
        with model_lock(host):
            frozen = run(
                study / 'bundles' / task_id,
                agent_dir,
                MODEL,
                PROFILE,
                seed=record['seed'],
                actions=budgets['actions'],
                repairs=budgets['repairs'],
                seconds=budgets['seconds'],
            )
        record['local_coding_seconds'] = round(time.monotonic() - coding_started, 2)
        if d2_gate is not None:
            record['d2_gate'] = d2_gate.summary()
            record['guidance'] = {
                'kind': f'd2:{d2_gate.mode}',
                'triggered': record['d2_gate'].get('checks', 0) > 0,
                'delivered': record['d2_gate'].get('failed', 0) > 0,
                'error': None,
            }
        if e2_ctrl is not None:
            traj_path = agent_dir / 'trajectory.json'
            messages = read_json(traj_path)['messages'] if traj_path.exists() else []
            record['e2_diagnosis'] = e2_ctrl.finalize(messages, frozen.get('events') or [])
            record['e2_diagnosis']['observations'] = e2_ctrl.observations
            wait = float(record['e2_diagnosis'].get('frontier_wait_seconds') or 0.0)
            record['frontier_wait_seconds'] = wait
            record['local_coding_seconds_net'] = round(record['local_coding_seconds'] - wait, 2)
            record['guidance'] = {
                'kind': f"e2:{record['e2_diagnosis'].get('controller', 'e2')}",
                'triggered': bool(record['e2_diagnosis'].get('trigger_observed')),
                'requested': bool(record['e2_diagnosis'].get('frontier_requested')),
                'delivered': bool(record['e2_diagnosis'].get('delivered')),
                'error': record['e2_diagnosis'].get('error_category'),
            }
            resp = record['e2_diagnosis'].get('response') or {}
            record['guidance_model'] = resp.get('model')
            if resp:
                record['usage']['guidance'] = [{
                    'usage': resp.get('usage'),
                    'cost_usd': resp.get('cost_usd'),
                    'latency_seconds': resp.get('latency_seconds'),
                }]

        record['frozen_result'] = str(agent_dir / 'result.json')
        record['raw_exit_status'] = frozen.get('status')
        record['exit_status'] = exit_status(frozen)
        record['frozen_error'] = {k: frozen.get(k) for k in ('error_type', 'error') if frozen.get(k)}
        record['n_actions'], record['n_repairs'] = frozen.get('actions', 0), frozen.get('repairs', 0)
        record['usage']['coding'] = coding_usage(agent_dir)
        for key in ('format_errors', 'model_calls', 'token_telemetry_complete', 'sampler_wire_verified',
                    'inference', 'context_events', 'elapsed_seconds', 'profile_config'):
            record[key] = frozen.get(key)
        record['model_digest'] = next(
            (m.get('digest') for m in (frozen.get('tags') or {}).get('models', []) if m.get('name') == MODEL),
            None,
        )
        solution = agent_dir / 'solution.py'
        if solution.exists():
            shutil.copyfile(solution, out / 'submission.py')
            record['submission_sha256'] = sha256_file(out / 'submission.py')
    except Exception as error:
        record['setup_error'] = f'{type(error).__name__}: {error}'
    finally:
        record['wall_seconds'] = round(time.monotonic() - started, 2)
        record['finished_utc'] = utc_now()
        (out / 'attempts.jsonl').write_text(''.join(json.dumps(a) + '\n' for a in attempts), encoding='utf-8')
        record['public_attempts'] = len(attempts)
        write_json(out / 'result.json', record)
    return record


def run_child_v2(spec, timeout=1000):
    """Run one enhanced_de attempt inside an isolated child process with hard outer timeout."""
    out = Path(spec['output'])
    out.parent.mkdir(parents=True, exist_ok=True)
    spec_path = out.parent / (out.name + '.spec.json')
    write_json(spec_path, spec)
    command = [sys.executable, '-m', 'enhanced_de', 'run-one', str(spec_path)]
    try:
        proc = subprocess.run(
            command,
            cwd=REPO,
            timeout=timeout,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
        )
        (out.parent / (out.name + '.log')).write_text(
            proc.stdout[-20000:] + '\n--- stderr ---\n' + proc.stderr[-20000:],
            encoding='utf-8',
        )
    except subprocess.TimeoutExpired:
        label = 'csc2108.eval-v2.run=agent-' + spec['run_id']
        ids = subprocess.run(
            ['docker', 'ps', '-aq', '--filter', 'label=' + label],
            capture_output=True, text=True,
        ).stdout.split()
        for cid in ids:
            subprocess.run(['docker', 'rm', '-f', cid], capture_output=True)
        record = read_json(out / 'result.json') if (out / 'result.json').exists() else {'run_id': spec['run_id']}
        record.update(
            exit_status='infra_error',
            raw_exit_status='OuterTimeout',
            outer_timeout_seconds=timeout,
            removed_containers=ids,
        )
        write_json(out / 'result.json', record)
    return read_json(out / 'result.json')


def run_batch_v2(batch_dir, specs, *, outer_timeout=1000):
    """Resumable sequential batch runner for enhanced_de attempts."""
    batch_dir = Path(batch_dir)
    batch_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for idx, spec in enumerate(specs, 1):
        out = Path(spec['output'])
        res_file = out / 'result.json'
        if res_file.is_file():
            rec = read_json(res_file)
            print(f"[{idx}/{len(specs)}] SKIP existing {spec['run_id']} ({rec.get('exit_status')})", flush=True)
            results.append(rec)
            continue
        if out.exists():
            # Clean up incomplete run dir cleanly
            dst = out.with_name(out.name + f'.incomplete-{int(time.time())}')
            out.rename(dst)
        print(f"[{idx}/{len(specs)}] RUN  {spec['run_id']} ({spec['arm']} / {spec['task_id']} s{spec.get('seed')})", flush=True)
        rec = run_child_v2(spec, timeout=outer_timeout)
        print(
            f"         DONE {spec['run_id']} exit={rec.get('exit_status')} "
            f"act={rec.get('n_actions')} wall={rec.get('wall_seconds')}s "
            f"sub={'yes' if rec.get('submission_sha256') else 'no'}",
            flush=True,
        )
        results.append(rec)
    return results


def evaluate_batch_v2(batch_dir, study):
    """Independent hidden scoring AFTER all attempts finish (mirrors guided_agent.runner.evaluate)."""
    study = Path(study)
    judge = backend.judge_client(study, 'hidden')
    info = judge.up()
    eval_dir = Path(batch_dir) / 'eval'
    eval_dir.mkdir(exist_ok=True)
    results = {}
    for result_path in sorted(Path(batch_dir).glob('*/result.json')):
        if '.incomplete-' in result_path.parent.name:
            continue
        record = read_json(result_path)
        run_id = record['run_id']
        ev_file = eval_dir / f'{run_id}.json'
        if ev_file.exists():
            results[run_id] = read_json(ev_file)
            continue
        submission = result_path.parent / 'submission.py'
        if record.get('submission_sha256') is None or not submission.exists():
            outcome = {'status': 'missing_submission', 'verdict': 'MISSING', 'passed': 0, 'total': 0}
        else:
            code = submission.read_bytes()
            if sha256_bytes(code) != record['submission_sha256']:
                outcome = {'status': 'infrastructure_error', 'error': 'submission hash mismatch'}
            else:
                res = judge.run(record['task_id'], code)
                outcome = {
                    k: res.get(k)
                    for k in ('status', 'passed', 'total', 'verdict_counts', 'judge_version',
                              'tests_sha256', 'code_sha256', 'error')
                }
        outcome |= {
            'run_id': run_id,
            'task_id': record['task_id'],
            'arm': record.get('arm'),
            'condition': record.get('condition'),
            'seed': record.get('seed'),
            'suite': 'hidden',
            'judge_tests_sha256': info.get('tests_sha256'),
            'evaluated_utc': utc_now(),
        }
        write_json(ev_file, outcome)
        results[run_id] = outcome
    return results
