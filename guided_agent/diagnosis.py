"""Condition E: one feedback-grounded frontier diagnosis inside the RUNNING local agent session.

Sequence (never a restart): local coding -> first qualifying judge-public failure -> one frontier
diagnosis of exactly that candidate and report -> the same mini-SWE-agent conversation, workspace,
counters and budgets continue.

* ``on_public_result`` is called by the judged environment after every recognized public test.
  The first qualifying candidate failure arms a pending diagnosis bound to the judged bytes.
* ``deliver`` is called by the agent right after that step's observation was added and before the
  next model query. It makes at most one provider call, suspends the local deadlines for exactly
  the frontier wait, and appends one user message. Provider failures are recorded and the agent
  continues with the original public feedback. No retries, no second request.
"""
import json
import secrets
import subprocess
import time
from pathlib import Path

from .common import sha256_bytes, sha256_text, utc_now, write_json
from . import guidance

QUALIFYING_VERDICTS = {'WA', 'RE', 'TLE', 'CE'}   # candidate-caused per the judge contract (judge.py)
MAX_PROGRAM_CHARS = 16000
MAX_REPORT_CHARS = 8000
SUBMISSION_CONTRACT = ('A Python 3.11 program saved at /workspace/solution.py that reads standard input and '
                       'writes standard output. The public judge runs it on each public case with a time limit '
                       'and compares its output line by line with the expected output (numbers are compared '
                       'exactly as decimals).')


def qualifies(result, source):
    """(qualifies, reason). Only a judged, non-empty candidate with a candidate-caused verdict qualifies."""
    status = result.get('status')
    if status == 'pass':
        return False, 'public_pass'
    if status != 'candidate_failure':
        return False, 'not_candidate_failure:' + str(status)
    if not source or not source.strip():
        return False, 'missing_candidate'
    verdict = (result.get('first_failure') or {}).get('verdict')
    if verdict not in QUALIFYING_VERDICTS:
        return False, 'non_qualifying_verdict:' + str(verdict)
    return True, 'qualifying:' + verdict


def _clip(text, cap, label):
    if len(text) <= cap:
        return text, False
    head, tail = text[: cap * 3 // 4], text[-cap // 4:]
    return f'{head}\n[... {label} truncated by the harness: {len(text)} characters in total ...]\n{tail}', True


def evidence_packet(*, statement, source, result, task_id, actions_used, action_limit, repairs_used, repair_limit,
                    seconds_left):
    program = source.decode('utf-8', 'replace')
    program_text, program_clipped = _clip(program, MAX_PROGRAM_CHARS, 'program')
    report = result.get('report') or ''
    report_text, report_clipped = _clip(report, MAX_REPORT_CHARS, 'report')
    nonce = secrets.token_hex(6)

    def block(name, body):
        return f'<<<DATA-{nonce} {name}>>>\n{body.rstrip()}\n<<<END-DATA-{nonce}>>>'

    first = result.get('first_failure') or {}
    user = '\n\n'.join([
        'PROBLEM STATEMENT\n' + block('statement', statement),
        'SUBMISSION CONTRACT\n' + SUBMISSION_CONTRACT,
        f"TESTED PROGRAM (sha256 {sha256_bytes(source)}, {len(source)} bytes)\n" + block('program', program_text),
        (f"PUBLIC TEST REPORT shown to the coding model (status {result.get('status')}, "
         f"{result.get('passed')}/{result.get('total')} public cases passed, first failing case "
         f"{first.get('name')}, verdict {first.get('verdict')})\n") + block('report', report_text),
        (f'LOCAL STATE: {actions_used} of {action_limit} actions used; {repairs_used} of {repair_limit} repair '
         f'groups used; about {int(max(0, seconds_left))} seconds of local coding time remain. The coding model '
         'will continue in the same session with the same files.'),
    ])
    return {
        'task_id': task_id, 'user_message': user, 'nonce': nonce,
        'statement_sha256': sha256_text(statement), 'candidate_sha256': sha256_bytes(source),
        'report_sha256': sha256_text(report), 'user_message_sha256': sha256_text(user),
        'verdict': first.get('verdict'), 'first_case': first.get('name'),
        'public_passed': result.get('passed'), 'public_total': result.get('total'),
        'program_clipped': program_clipped, 'report_clipped': report_clipped,
        'judge_code_sha256': result.get('code_sha256'), 'judge_tests_sha256': result.get('tests_sha256'),
    }


# ----------------------------------------------------------------------------- providers
class DiagnosisFailure(RuntimeError):
    def __init__(self, category, detail=''):
        super().__init__(f'{category}: {detail}')
        self.category, self.detail = category, detail


class CodexDiagnoser:
    """Fresh, isolated, tool-less Codex inference at the moment of failure (the default provider)."""
    name = 'codex-live'

    def __init__(self, work_root, model='gpt-6.2-sol', effort='medium', timeout=300):
        self.work_root, self.model, self.effort, self.timeout = Path(work_root), model, effort, timeout

    def __call__(self, system, user, evidence_dir, packet=None):
        from . import providers
        try:
            result = providers.codex_infer(system=system, user=user, evidence=evidence_dir, work_root=self.work_root,
                                           model=self.model, effort=self.effort, timeout=self.timeout)
        except subprocess.TimeoutExpired:
            raise DiagnosisFailure('timeout', f'{self.timeout} s') from None
        except providers.CodexIsolationError as error:
            raise DiagnosisFailure('isolation_violation', str(error)) from None
        except Exception as error:
            raise DiagnosisFailure('provider_error', f'{type(error).__name__}: {error}') from None
        return {'text': result['text'], 'provider': 'codex-live', 'model': self.model, 'reasoning_effort': self.effort,
                'usage': {'codex_reported': result['usage']}, 'latency_seconds': None,
                'harness_wall_seconds': result['wall_seconds'], 'cost_usd': None, 'isolation': result['isolation']}


class ApiDiagnoser:
    """One ledgered direct-API request; refuses (before sending) when the ledger ceiling would be exceeded."""
    name = 'openai-api'

    def __init__(self, ledger_path, purpose, effort='medium', max_completion_tokens=8000, timeout=300, meta=None):
        self.ledger_path, self.purpose, self.effort = ledger_path, purpose, effort
        self.max_completion_tokens, self.timeout, self.meta = max_completion_tokens, timeout, meta or {}

    def __call__(self, system, user, evidence_dir, packet=None):
        from . import providers
        Path(evidence_dir).mkdir(parents=True, exist_ok=False)
        try:
            result = providers.api_chat(messages=[{'role': 'system', 'content': system}, {'role': 'user', 'content': user}],
                                        ledger_path=self.ledger_path, max_completion_tokens=self.max_completion_tokens,
                                        effort=self.effort, timeout=self.timeout,
                                        entry={'kind': 'diagnosis', 'prompt_id': 'diagnosis-v1', 'purpose': self.purpose,
                                               **self.meta})
        except providers.ApiRequestError as error:
            raise DiagnosisFailure('transport_error', str(error)) from None
        except RuntimeError as error:  # ledger refusal happens before any request is sent
            raise DiagnosisFailure('budget_exhausted', str(error)) from None
        write_json(Path(evidence_dir) / 'response.json', result['payload'])
        if result['finish_reason'] != 'stop':
            raise DiagnosisFailure('incomplete_response', 'finish_reason=' + str(result['finish_reason']))
        return {'text': result['text'], 'provider': 'openai-api', 'model': result['api_model'],
                'observed_model': result['payload'].get('model'), 'reasoning_effort': self.effort,
                'usage': result['usage'], 'latency_seconds': result['latency_seconds'], 'cost_usd': result['cost_usd'],
                'request_id': result['request_id'], 'ledger_index': result['ledger_index'],
                'isolation': {'mechanism': 'direct HTTPS request; statement, failed program and public report only'}}


class FixedDiagnoser:
    """Deterministic provider for tests and synthetic fixtures. Never presented as a live diagnosis."""
    name = 'fixed'

    def __init__(self, text=None, error=None, delay=0.0):
        self.text, self.error, self.delay, self.calls = text, error, delay, 0

    def __call__(self, system, user, evidence_dir, packet=None):
        self.calls += 1
        Path(evidence_dir).mkdir(parents=True, exist_ok=False)
        if self.delay:
            time.sleep(self.delay)
        if self.error:
            raise DiagnosisFailure(*self.error)
        return {'text': self.text, 'provider': 'fixed', 'model': None, 'usage': None, 'latency_seconds': self.delay,
                'cost_usd': None, 'isolation': {'mechanism': 'fixed text (test or synthetic fixture)'}}


class ReplayDiagnoser:
    """Replays a recorded diagnosis only for the identical evidence packet (same candidate and report)."""
    name = 'replay'

    def __init__(self, path):
        self.path = Path(path)

    def __call__(self, system, user, evidence_dir, packet=None):
        recorded = json.loads(self.path.read_text(encoding='utf-8'))
        Path(evidence_dir).mkdir(parents=True, exist_ok=False)
        wanted = (recorded['packet']['candidate_sha256'], recorded['packet']['report_sha256'],
                  recorded['packet']['statement_sha256'])
        if packet is None or (packet['candidate_sha256'], packet['report_sha256'], packet['statement_sha256']) != wanted:
            raise DiagnosisFailure('replay_mismatch', 'recorded diagnosis belongs to a different candidate/report')
        return {'text': recorded['response']['text'], 'provider': 'replay:' + recorded['response']['provider'],
                'model': recorded['response'].get('model'), 'usage': None, 'latency_seconds': 0.0, 'cost_usd': None,
                'isolation': {'mechanism': 'recorded diagnosis replay', 'source': str(self.path)}}


def make_provider(spec, study):
    kind = spec.get('provider', 'codex')
    timeout = spec.get('timeout', 300)
    if kind == 'codex':
        return CodexDiagnoser(study / 'codex-work', model=spec.get('model', 'gpt-6.2-sol'),
                              effort=spec.get('effort', 'medium'), timeout=timeout)
    if kind == 'api':
        if not spec.get('purpose'):
            raise ValueError('API diagnosis requires a purpose')
        return ApiDiagnoser(study / 'api-ledger.json', spec['purpose'], effort=spec.get('effort', 'medium'),
                            max_completion_tokens=spec.get('max_completion_tokens', 8000), timeout=timeout,
                            meta={'condition': 'E'})
    if kind == 'fixed':
        return FixedDiagnoser(text=spec.get('text'), error=tuple(spec['error']) if spec.get('error') else None,
                              delay=spec.get('delay', 0.0))
    if kind == 'replay':
        return ReplayDiagnoser(spec['path'])
    raise ValueError('Unknown diagnosis provider ' + str(kind))


# ----------------------------------------------------------------------------- controller
class DiagnosisController:
    """At-most-once trigger, delivery into the live conversation, and continuous local budgets."""

    def __init__(self, *, provider, statement, task_id, out_dir, prompt_id='diagnosis-v1', delivery='deliver-v1',
                 max_wait_seconds=300):
        self.provider, self.statement, self.task_id = provider, statement, task_id
        self.out_dir = Path(out_dir)
        self.prompt_id, self.delivery = prompt_id, delivery
        self.system = guidance.PROMPTS[prompt_id][1]
        self.max_wait_seconds = max_wait_seconds
        self.pending = None
        self.observations = []
        self.record = {'assigned': True, 'prompt_id': prompt_id, 'delivery_template': delivery,
                       'provider': getattr(provider, 'name', type(provider).__name__),
                       'trigger_observed': False, 'trigger_reason': None, 'frontier_requested': False,
                       'frontier_returned': False, 'delivered': False, 'error': None, 'error_category': None,
                       'frontier_wait_seconds': 0.0, 'later_public_failures': 0}

    # called by the environment (inside the local action that ran the public test)
    def on_public_result(self, *, result, source, digest, budget, deadline, now=None):
        now = time.monotonic() if now is None else now
        ok, reason = qualifies(result, source)
        self.observations.append({'action': budget.actions, 'status': result.get('status'), 'reason': reason,
                                  'source_sha256': digest})
        if self.record['trigger_observed']:
            if result.get('status') == 'candidate_failure':
                self.record['later_public_failures'] += 1
            return False
        if not ok:
            return False
        packet = evidence_packet(statement=self.statement, source=source, result=result, task_id=self.task_id,
                                 actions_used=budget.actions, action_limit=budget.action_limit,
                                 repairs_used=min(budget.repairs, budget.repair_limit), repair_limit=budget.repair_limit,
                                 seconds_left=deadline - now)
        self.record.update(trigger_observed=True, trigger_reason=reason, trigger_action=budget.actions,
                           trigger_utc=utc_now(), local_seconds_left_at_trigger=round(deadline - now, 2),
                           actions_left_at_trigger=budget.action_limit - budget.actions,
                           repairs_used_at_trigger=budget.repairs,
                           packet={k: v for k, v in packet.items() if k != 'user_message'})
        self.pending = packet
        return True

    def observe_infrastructure_error(self, *, action, error):
        self.observations.append({'action': action, 'status': 'infrastructure_error', 'reason': 'infrastructure_error',
                                  'error': error})

    # called by the agent after the triggering step's observation was appended, before the next query
    def deliver(self, agent):
        packet, self.pending = self.pending, None
        if packet is None:
            return None
        env = agent.env
        budget = env.budget
        if budget.actions >= budget.action_limit:
            self.record.update(error='no local action left to use a diagnosis', error_category='no_local_budget')
            return None
        self.out_dir.mkdir(parents=True, exist_ok=True)
        write_json(self.out_dir / 'packet.json', packet)
        self.record['frontier_requested'] = True
        self.record['requested_utc'] = utc_now()
        started_mono, started_wall = time.monotonic(), time.time()
        response = None
        try:
            response = self.provider(self.system, packet['user_message'], self.out_dir / 'provider', packet=packet)
            text = response.get('text') if isinstance(response, dict) else None
            if not isinstance(text, str) or not text.strip():
                raise DiagnosisFailure('empty_diagnosis')
            problems = guidance.validate('diagnosis', text)
            if problems:
                raise DiagnosisFailure('invalid_format', '; '.join(problems))
        except DiagnosisFailure as error:
            self.record.update(error=str(error), error_category=error.category)
            text = None
        except Exception as error:  # any other provider defect: recorded, never retried
            self.record.update(error=f'{type(error).__name__}: {error}', error_category='provider_error')
            text = None
        finally:
            waited = time.monotonic() - started_mono
            # Suspend local time for exactly the frontier wait: the monotonic task deadline (sandbox commands and
            # model request timeouts) and mini-swe-agent's wall-clock start (TimeExceeded) move forward together.
            env.deadline += waited
            if hasattr(agent, '_start_time'):
                agent._start_time += time.time() - started_wall
            self.record['frontier_wait_seconds'] = round(waited, 3)
        if response is not None and isinstance(response, dict):
            self.record['frontier_returned'] = bool(response.get('text'))
            self.record['response'] = {k: v for k, v in response.items() if k != 'text'}
        if text is None:
            write_json(self.out_dir / 'diagnosis.json', {'packet': {k: v for k, v in packet.items()},
                                                         'response': None, 'record': self.record})
            return None
        message = guidance.DIAGNOSIS_DELIVERY[self.delivery].format(
            actions_left=budget.action_limit - budget.actions, diagnosis=text.strip())
        added = agent.add_messages({'role': 'user', 'content': message,
                                    'extra': {'interrupt_type': 'FrontierDiagnosis',
                                              'candidate_sha256': packet['candidate_sha256'],
                                              'report_sha256': packet['report_sha256'],
                                              'diagnosis_sha256': sha256_text(text)}})
        self.record.update(delivered=True, delivered_utc=utc_now(), diagnosis_sha256=sha256_text(text),
                           diagnosis_words=len(text.split()), delivered_message_index=len(agent.messages) - 1,
                           delivered_after_action=budget.actions, soft_code_flags=guidance.soft_flags(text))
        write_json(self.out_dir / 'diagnosis.json', {'packet': packet, 'response': (response or {}) | {'text': text},
                                                     'delivered_message': message, 'record': self.record})
        return added

    def finalize(self, messages, events):
        """Post-hoc: was the diagnosis followed by local actions, edits and retests?"""
        index = self.record.get('delivered_message_index')
        if index is None:
            return self.record
        after = messages[index + 1:]
        self.record['assistant_messages_after'] = sum(m.get('role') == 'assistant' for m in after)
        delivered_action = self.record.get('delivered_after_action', 0)
        later = [e for e in events if (e.get('action') or 0) > delivered_action]
        self.record['local_actions_after'] = len(later)
        self.record['public_tests_after'] = sum(bool(e.get('recognized_public_test')) for e in later)
        trigger_hash = self.record['packet']['candidate_sha256']
        self.record['candidate_changed_after'] = any(e.get('source_sha256') not in (None, trigger_hash) for e in later)
        tests = [e for e in later if e.get('recognized_public_test')]
        self.record['public_pass_after'] = any(e.get('public_status') == 'pass' for e in tests)
        return self.record
