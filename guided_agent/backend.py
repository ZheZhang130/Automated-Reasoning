"""Run the frozen ``local_eval_v2.runtime.run`` bytecode for A, C and D.

Only two globals of the frozen function are rebound, identically for every condition:

* ``Agent``       -> subclass that appends the upfront guidance block to the first user message
                     (A keeps the frozen ``{{task}}`` template byte-for-byte).
* ``Environment`` -> subclass that routes the recognized public-test command
                     (``python -I /public/check.py``) to the team's judge-public, returning its
                     ``report`` as the observation. All other commands run in the frozen sandbox.

Model configuration, sampler wiring, prompts, budgets, telemetry, GPU exclusivity, candidate
extraction and cleanup are the unmodified frozen code. Host differences come from the existing
``local_agent`` adapters (Windows: original globals; portable: ``portable.adapted_run``).
Optional ACI interventions (``aci``) are opt-in, labelled, and applied identically to A/C/D.
"""
import hashlib
import importlib
import re
import sys
import time
import types
from pathlib import Path

from .common import REPO, utc_now

JUDGE_NAME = 'csc2108re-judge-{suite}'
WRITE_PATTERN = re.compile(r'(?:cat|tee)\s*>?\s*/workspace/solution\.py|>\s*/workspace/solution\.py')

# Opt-in replacement for the frozen FORMAT_ERROR (rebound global); same variables, more specific length advice.
FORMAT_ERROR_TRUNCATION_V1 = """Rejected: {{error}}. No action from that response ran.
Return ONE complete command block with a closing fence. Use a literal heredoc for multiline files.
```mswea_bash_command
pwd
```
{% if finish_reason == 'length' %}Your response reached the 4096-token output limit before its command block closed, so nothing was saved. Do not reason or brainstorm inside the file. Decide the approach in at most 5 short lines of plain text, then write the complete program with few or no comments.{% endif %}"""


def aci_globals(aci):
    """Frozen-function globals replaced by an ACI intervention (empty for the original control)."""
    return {'FORMAT_ERROR': FORMAT_ERROR_TRUNCATION_V1} if (aci or {}).get('truncation_note') else {}


def judge_client(study, suite):
    """One container per study root and suite, so separate studies never recreate each other's judge."""
    sys.path.insert(0, str(REPO / 'judge'))
    from judgekit import Judge
    suffix = hashlib.sha256(str(Path(study).resolve()).encode()).hexdigest()[:8]
    return Judge(suite, root=study / 'judge', name=JUDGE_NAME.format(suite=suite) + '-' + suffix)


def frozen_runtime(host_settings):
    if host_settings.backend == 'portable':
        from local_agent.portable import load_runtime
        return load_runtime(host_settings)
    host_settings.initialize()
    sys.path.insert(0, str(REPO / 'local_eval_v2'))
    return importlib.import_module('runtime')


def host_base_function(runtime, host_settings):
    if host_settings.backend == 'portable':
        from local_agent.portable import adapted_run, verify_images
        # As local_agent.portable.worker does: an external foreground Ollama may not write this log.
        log = host_settings.root / 'logs/ollama-project.stderr.log'
        log.parent.mkdir(parents=True, exist_ok=True)
        log.touch(exist_ok=True)
        return adapted_run(runtime, host_settings, verify_images(host_settings)), 'portable.adapted_run'
    return runtime.run, 'windows-frozen-globals'


def make_classes(runtime, *, guidance_text, template, judge, task_id, attempts, aci=None):
    aci = aci or {}
    v3 = runtime.v3

    class GuidedAgent(runtime.Agent):
        def __init__(self, *args, instance_template, **kwargs):
            if guidance_text is not None:
                instance_template = template
            super().__init__(*args, instance_template=instance_template, **kwargs)
            self.instance_template_used = instance_template
            self._previous_command = None
            self.repeat_guards = 0

        def run(self, task='', **kwargs):
            if guidance_text is not None:
                kwargs = kwargs | {'guide': guidance_text}
            return super().run(task, **kwargs)

        def execute_actions(self, message):
            # aci repeat_guard (aci-v2): an action byte-identical to the previous executed action cannot change
            # the sandbox state. It is not executed, its duplicate assistant turn is dropped from the history
            # (so the context does not accumulate a self-reinforcing repetition), and the model is told why.
            # It still consumes a model call (step limit) but no action.
            actions = message.get('extra', {}).get('actions', [])
            command = actions[0].get('command') if len(actions) == 1 else None
            if aci.get('repeat_guard') and command is not None and command == self._previous_command:
                if self.messages and self.messages[-1] is message:
                    self.messages.pop()
                self.repeat_guards += 1
                failed = self.env.budget.failed_hash is not None
                self.env.evidence.append({'command': command, 'repeat_guard': True, 'action': self.env.budget.actions})
                text = ('[harness] Not executed: this command is identical to your previous command, so repeating '
                        'it cannot change anything. ' +
                        ('/workspace/solution.py still holds the program that failed the public tests; change its '
                         'logic before testing again.' if failed else
                         'If the program has not been tested yet, run python -I /public/check.py; otherwise choose a '
                         'different next action.'))
                return self.add_messages({'role': 'user', 'content': text,
                                          'extra': {'interrupt_type': 'RepeatGuard', 'model_response': command}})
            self._previous_command = command
            return super().execute_actions(message)

    class JudgedEnvironment(runtime.Environment):
        def execute(self, action, cwd='', *, timeout=None):
            command = action.get('command', '')
            if isinstance(command, str) and runtime.TEST_PATTERN.fullmatch(command):
                return self._public_judge(command)
            before = self.last_candidate  # the frozen environment's snapshot after the previous action
            output = super().execute(action, cwd, timeout=timeout)
            if aci.get('unchanged_source_note') and isinstance(command, str) and WRITE_PATTERN.search(command) \
                    and before is not None and self.last_candidate == before:
                note = '[harness] /workspace/solution.py is byte-for-byte unchanged by this command.'
                if hashlib.sha256(before).hexdigest() == self.budget.failed_hash:
                    note += (' This exact program already failed the public tests, so rewriting it identically '
                             'cannot fix the failure. Change the program logic.')
                output['output'] = (output.get('output') or '') + note + '\n'
                self.evidence[-1]['aci_note'] = 'unchanged_source'
            return output

        def _public_judge(self, command):
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise v3.limits('Deadline')
            self.budget.before()
            source = self.snapshot()
            started = time.monotonic()
            digest = hashlib.sha256(source).hexdigest() if source is not None else None
            result = judge.run(task_id, source or b'', timeout=max(10.0, min(120.0, remaining)))
            attempts.append({'seq': len(attempts) + 1, 'time': utc_now(), 'result': result, 'delivered': True,
                             'action': self.budget.actions, 'source_sha256': digest})
            self.last_candidate = source
            if result.get('status') == 'infrastructure_error' or result.get('task_id') != task_id \
                    or result.get('suite') != 'public':
                attempts[-1]['delivered'] = False
                self.evidence.append({'command': command, 'action': self.budget.actions, 'source_sha256': digest,
                                      'judge_infrastructure_error': result.get('error') or result.get('status')})
                raise v3.limits('InfrastructureError')
            returncode = 0 if result['status'] == 'pass' else 1
            report = result.get('report', '')
            if aci.get('unchanged_source_note') and returncode and digest is not None and digest == self.budget.failed_hash:
                report += ('\n[harness] This exact program already failed these public tests before; '
                           'change the program before testing again.')
                aci_flag = 'retest_unchanged'
            else:
                aci_flag = None
            output = {'output': report, 'returncode': returncode, 'exception_info': ''}
            self.evidence.append({'command': command, 'action': self.budget.actions,
                                  'elapsed_seconds': time.monotonic() - started, 'source_sha256': digest,
                                  'recognized_public_test': True, 'public_status': result['status'],
                                  'judge': {k: result.get(k) for k in ('status', 'passed', 'total', 'verdict_counts',
                                                                       'code_sha256', 'tests_sha256', 'judge_version')},
                                  'aci_note': aci_flag, **output})
            self.budget.tested(digest, returncode)
            return output

    return GuidedAgent, JudgedEnvironment


def bound_run(base_function, agent_cls, env_cls, extra_globals=None):
    bindings = dict(base_function.__globals__) | {'Agent': agent_cls, 'Environment': env_cls} | (extra_globals or {})
    function = types.FunctionType(base_function.__code__, bindings, base_function.__name__,
                                  base_function.__defaults__, base_function.__closure__)
    function.__kwdefaults__ = base_function.__kwdefaults__
    return function
