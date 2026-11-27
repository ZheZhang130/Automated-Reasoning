"""Phase 4 supporting investigation: bounded shared local-agent interface (L5 + L4).

Strictly separate from `frozen-v6` (`interface = "l5-l4-experimental"`). Never modifies
any frozen file; wraps `runner_v2` via `guided_agent.backend.bound_run` subclasses to test:
- L5 (Deliberation carry-over): when Ollama stops at `done_reason == 'length'` with a
  FormatError, keep the last ~1,200 chars of discarded reasoning inside the rejection
  feedback (instead of dropping it completely) so the model does not restart from zero.
- L4 (Compact write receipt): when a non-public-test command exits 0 with empty output
  and `/workspace/solution.py` exists, append a 1-line digest/line-count receipt so
  the model avoids blind identical-rewrite loops.

Evaluated as a matched factorial across A, C (frozen plan-v1, 0 calls), and D2-oracle
on a compact dev subset so we see whether interface relief helps A/D2 without harming C.
"""

import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path

from minisweagent.exceptions import FormatError

from guided_agent import backend, guidance
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
    sha256_file,
    settings,
    study_root,
    utc_now,
    write_json,
)
from guided_agent.runner import coding_usage, exit_status, source_state
from guided_agent.tasks import load_statement

from . import d2_contract, run_experiments as rexp, runner_v2


DEFAULT_STUDY = Path(r'E:\CSC2108Local\enhanced-de-v2-study')
FROZEN_PLANS_DIR = REPO / 'results' / 'final-main' / 'guidance' / 'final-plans'
CARRYOVER_CHARS = 1200


def make_l5_l4_classes(
    runtime,
    *,
    judge,
    task_id,
    attempts,
    public_cases=None,
    guidance_text=None,
    template=None,
    d2_gate=None,
):
    """Build L5 (deliberation carry-over) + L4 (write receipt) experimental classes."""
    base_agent_cls, base_env_cls = runner_v2.make_enhanced_classes(
        runtime,
        judge=judge,
        task_id=task_id,
        attempts=attempts,
        public_cases=public_cases,
        guidance_text=guidance_text,
        template=template,
        d2_gate=d2_gate,
        e2_controller=None,
    )

    class L5Agent(base_agent_cls):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.l5_carryovers = 0
            self._pending_carryover = None

        def query(self):
            if self._pending_carryover:
                note = self._pending_carryover
                self._pending_carryover = None
                self.add_messages({'role': 'user', 'content': note})
            return super().query()

        def step(self):
            try:
                return super().step()
            except FormatError:
                raw_content = ''
                done_reason = None
                model_obj = getattr(self, 'model', None)
                last_resp = getattr(model_obj, '_last_response', None) if model_obj is not None else None
                if isinstance(last_resp, dict):
                    done_reason = last_resp.get('done_reason')
                    raw_content = last_resp.get('content') or ''
                if not raw_content:
                    for msg in reversed(getattr(self, 'messages', [])):
                        if msg.get('role') == 'assistant':
                            raw_content = msg.get('content') or ''
                            break
                if done_reason == 'length' and raw_content.strip():
                    tail = raw_content[-CARRYOVER_CHARS:].strip()
                    self.l5_carryovers += 1
                    self._pending_carryover = (
                        '[L5 deliberation carry-over — your prior response hit the 4096-token output cap. '
                        'Do NOT repeat your derivation or write long comments. Use your conclusion below and '
                        'immediately emit ONE complete, concise command writing /workspace/solution.py:]\n'
                        f'<<<TRUNCATED-TAIL>>>\n{tail}\n<<<END-TAIL>>>'
                    )
                raise

    class L4Environment(base_env_cls):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.l4_receipts = 0
            self._last_written_digest = None

        def execute(self, action, cwd=''):
            out = super().execute(action, cwd=cwd)
            cmd = action.get('command', '') if isinstance(action, dict) else str(action)
            if (
                out.get('returncode') == 0
                and not (out.get('output') or '').strip()
                and 'solution.py' in cmd
                and 'check.py' not in cmd
            ):
                src = self._read_solution()
                if src:
                    dig = hashlib.sha256(src).hexdigest()[:12]
                    n_lines = src.count(b'\n') + (0 if src.endswith(b'\n') else 1)
                    dup = ' (IDENTICAL to previous write — change logic before retesting!)' if dig == self._last_written_digest else ''
                    self._last_written_digest = dig
                    self.l4_receipts += 1
                    out['output'] = (
                        f'[Workspace receipt: /workspace/solution.py saved, {n_lines} lines, '
                        f'sha256={dig}{dup}. Run python -I /public/check.py next.]\n'
                    )
            return out

    return L5Agent, L4Environment


def run_l5_l4_attempt(spec):
    """Run one L5+L4 experimental interface attempt (strictly tagged separate from frozen-v6)."""
    host = settings(spec.get('backend', 'auto'))
    study = study_root(host, spec.get('study'))
    task_id = spec['task_id']
    arm = spec['arm']
    out = Path(spec['output'])
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / 'spec.json', spec)
    started_utc = utc_now()
    statement = load_statement(study, task_id)
    public_cases = runner_v2.load_public_cases(study, task_id)

    record = {
        'run_id': spec['run_id'],
        'task_id': task_id,
        'condition': spec.get('condition', 'L5L4'),
        'arm': arm,
        'interface_regime': 'l5-l4-experimental',
        'coding_model': MODEL,
        'exit_status': 'infra_error',
        'submission_sha256': None,
        'n_actions': 0,
        'n_repairs': 0,
        'guidance': {'kind': arm, 'triggered': False, 'delivered': False, 'error': None},
        'usage': {'coding': [], 'guidance': []},
        'wall_seconds': None,
        'host': host_identity()['node'],
        'backend': 'enhanced_de/l5-l4-experimental',
        'profile': PROFILE,
        'seed': spec.get('seed', SEED),
        'started_utc': started_utc,
        'cohort': spec.get('cohort'),
        'batch': spec.get('batch'),
        'source': source_state(),
    }
    attempts = []
    started = time.monotonic()
    try:
        from local_agent.cli import verify
        from local_agent.platform_support import model_lock

        record['frozen_verification'] = {
            k: v for k, v in verify(settings=host).items()
            if k in ('frozen_files_verified', 'model_digest', 'ollama')
        }
        d2_gate = None
        guidance_text = template = None
        if spec.get('d2'):
            bank = read_json(spec['d2']['bank_path'])
            d2_gate = d2_contract.D2GateChecker(bank, mode=spec['d2'].get('mode', 'oracle'))
        if spec.get('plan_path'):
            plan_obj = read_json(spec['plan_path'])
            guidance_text = plan_obj['text']
            from guided_agent.agent_config import PLAN_TEMPLATE
            template = PLAN_TEMPLATE

        runtime = backend.frozen_runtime(host)
        base, adapter = backend.host_base_function(runtime, host)
        judge = backend.judge_client(study, 'public')
        judge.up()
        agent_cls, env_cls = make_l5_l4_classes(
            runtime,
            judge=judge,
            task_id=task_id,
            attempts=attempts,
            public_cases=public_cases,
            guidance_text=guidance_text,
            template=template,
            d2_gate=d2_gate,
        )
        run = backend.bound_run(base, agent_cls, env_cls, {})
        agent_dir = out / ('agent-' + spec['run_id'])
        with model_lock(host):
            frozen = run(
                study / 'bundles' / task_id,
                agent_dir,
                MODEL,
                PROFILE,
                seed=record['seed'],
                actions=ACTIONS,
                repairs=REPAIRS,
                seconds=SECONDS,
            )
        if d2_gate is not None:
            record['d2_gate'] = d2_gate.summary()
            record['guidance'] = {
                'kind': f'd2:{d2_gate.mode}',
                'triggered': record['d2_gate'].get('checks', 0) > 0,
                'delivered': record['d2_gate'].get('failed', 0) > 0,
                'error': None,
            }
        elif guidance_text is not None:
            record['guidance'] = {'kind': 'plan-v1', 'triggered': True, 'delivered': True, 'error': None}
        record['raw_exit_status'] = frozen.get('status')
        record['exit_status'] = exit_status(frozen)
        record['n_actions'], record['n_repairs'] = frozen.get('actions', 0), frozen.get('repairs', 0)
        record['usage']['coding'] = coding_usage(agent_dir)
        record['format_errors'] = frozen.get('format_errors')
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
        write_json(out / 'result.json', record)
    return record


# Compact 8-pair matched factorial dev probe: 4 truncation-stall + 4 PPHF
PHASE4_PAIRS = [
    ('lcb-atcoder-abc390_d', 2108, 'trunc_c_pass'),
    ('lcb-atcoder-abc391_d', 2110, 'trunc_c_pass'),
    ('lcb-atcoder-abc394_e', 2108, 'trunc_c_pass'),
    ('lcb-atcoder-arc195_b', 2108, 'trunc_c_pass'),
    ('lcb-atcoder-abc387_c', 2108, 'pphf_wa'),
    ('lcb-atcoder-abc400_c', 2109, 'pphf_wa'),
    ('lcb-atcoder-arc194_d', 2109, 'pphf_wa'),
    ('lcb-atcoder-arc195_b', 2109, 'pphf_wa'),
]


def main():
    p = argparse.ArgumentParser(description='Run Phase 4 L5+L4 experimental shared-interface factorial probe')
    p.add_argument('--study', default=str(DEFAULT_STUDY))
    p.add_argument('--arms', default='A-L5L4,D2-oracle-L5L4,C-L5L4')
    args = p.parse_args()

    study = Path(args.study)
    arms = [a.strip() for a in args.arms.split(',') if a.strip()]
    batch_name = 'phase4-l5l4-interface-probe'
    batch_dir = study / 'runs' / batch_name
    batch_dir.mkdir(parents=True, exist_ok=True)

    specs = []
    for arm in arms:
        for tid, seed, stratum in PHASE4_PAIRS:
            short = tid.replace('lcb-atcoder-', '')
            rid = f'{batch_name}-{short}-{arm}-s{seed}'
            sp = {
                'run_id': rid,
                'task_id': tid,
                'seed': seed,
                'arm': arm,
                'condition': arm,
                'cohort': f'phase4-l5l4:{stratum}',
                'batch': batch_name,
                'study': str(study),
                'output': str(batch_dir / rid),
            }
            if arm == 'D2-oracle-L5L4':
                sp['d2'] = {'bank_path': str(study / 'd2_banks' / 'codex' / f'{tid}.bank.json'), 'mode': 'oracle'}
            elif arm == 'C-L5L4':
                sp['plan_path'] = str(FROZEN_PLANS_DIR / f'{tid}.plan-v1.api.json')
            specs.append(sp)

    print(f'=== Phase 4 L5+L4 Experimental Interface Probe ({len(specs)} runs -> {batch_dir}) ===', flush=True)
    for idx, sp in enumerate(specs, 1):
        out = Path(sp['output'])
        if (out / 'result.json').is_file():
            rec = read_json(out / 'result.json')
            print(f"[{idx}/{len(specs)}] SKIP existing {sp['run_id']} ({rec.get('exit_status')})", flush=True)
            continue
        if out.exists():
            out.rename(out.with_name(out.name + f'.incomplete-{int(time.time())}'))
        print(f"[{idx}/{len(specs)}] RUN  {sp['run_id']}", flush=True)
        rec = run_l5_l4_attempt(sp)
        print(f"         DONE {sp['run_id']} exit={rec.get('exit_status')} act={rec.get('n_actions')} wall={rec.get('wall_seconds')}s sub={'yes' if rec.get('submission_sha256') else 'no'}", flush=True)

    print(f'--- Hidden evaluation for {batch_dir} ---', flush=True)
    runner_v2.evaluate_batch_v2(batch_dir, study)
    summary = rexp.summarize_batch(batch_dir, compare_final_main=True)
    write_json(batch_dir / 'summary.json', summary)
    print(json.dumps(summary['by_arm'], indent=2), flush=True)


if __name__ == '__main__':
    main()
