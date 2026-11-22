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
import sys
import time
import types

from .common import REPO, utc_now

JUDGE_NAME = 'csc2108re-judge-{suite}'


def judge_client(study, suite):
    sys.path.insert(0, str(REPO / 'judge'))
    from judgekit import Judge
    return Judge(suite, root=study / 'judge', name=JUDGE_NAME.format(suite=suite))


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

        def run(self, task='', **kwargs):
            if guidance_text is not None:
                kwargs = kwargs | {'guide': guidance_text}
            return super().run(task, **kwargs)

    class JudgedEnvironment(runtime.Environment):
        def execute(self, action, cwd='', *, timeout=None):
            command = action.get('command', '')
            if isinstance(command, str) and runtime.TEST_PATTERN.fullmatch(command):
                return self._public_judge(command)
            output = super().execute(action, cwd, timeout=timeout)
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
            output = {'output': report, 'returncode': returncode, 'exception_info': ''}
            self.evidence.append({'command': command, 'action': self.budget.actions,
                                  'elapsed_seconds': time.monotonic() - started, 'source_sha256': digest,
                                  'recognized_public_test': True, 'public_status': result['status'],
                                  'judge': {k: result.get(k) for k in ('status', 'passed', 'total', 'verdict_counts',
                                                                       'code_sha256', 'tests_sha256', 'judge_version')},
                                  **output})
            self.budget.tested(digest, returncode)
            return output

    return GuidedAgent, JudgedEnvironment


def bound_run(base_function, agent_cls, env_cls, extra_globals=None):
    bindings = dict(base_function.__globals__) | {'Agent': agent_cls, 'Environment': env_cls} | (extra_globals or {})
    function = types.FunctionType(base_function.__code__, bindings, base_function.__name__,
                                  base_function.__defaults__, base_function.__closure__)
    function.__kwdefaults__ = base_function.__kwdefaults__
    return function
