"""Run the frozen ``local_eval_v2.runtime.run`` bytecode for every condition.

Only globals of the frozen function are rebound, identically for every condition:

* ``Agent``       -> ``GuidedAgent``: the first user message template (C/D guidance block, the shared agent's
                     self-plan block; A keeps the frozen ``{{task}}`` template byte for byte) and, for E, one
                     diagnosis message delivered into the running conversation.
* ``Environment`` -> ``JudgedEnvironment``: the recognized public-test command (``python -I /public/check.py``)
                     goes to the team's judge-public and its ``report`` is the observation. Every other command runs
                     in the frozen sandbox.

Model configuration, sampler wiring, prompts, budgets, telemetry, GPU exclusivity, candidate extraction and cleanup
are the unmodified frozen code. Host differences come from the existing ``local_agent`` adapters (Windows: original
globals; portable: ``portable.adapted_run``). B additionally rebinds the model class (``frontier_coder``).
"""
import hashlib
import importlib
import sys
import time
import types
from pathlib import Path

from .common import REPO, utc_now

JUDGE_NAME = 'csc2108re-judge-{suite}'


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


def make_classes(runtime, *, guidance_text, template, judge, task_id, attempts, diagnosis=None, self_planner=None):
    """``diagnosis`` (E) is a ``diagnosis.DiagnosisController``; ``self_planner`` is the shared agent's
    ``agent_config.SelfPlanner`` (None for ``frozen-v6``)."""
    v3 = runtime.v3

    class GuidedAgent(runtime.Agent):
        def __init__(self, *args, instance_template, **kwargs):
            if guidance_text is not None or self_planner is not None:
                instance_template = template
            super().__init__(*args, instance_template=instance_template, **kwargs)
            self.instance_template_used = instance_template
            if self_planner is not None and self_planner.record.get('wall_seconds'):
                # Equal local opportunity (as for C's plan): the self-plan call ran after the frozen deadline was
                # set, so the coding deadline is moved back by exactly that call's duration. The container was
                # created after the call, so its lifetime still covers the full coding budget.
                self.env.deadline += self_planner.record['wall_seconds']
                self_planner.record['deadline_extension_seconds'] = self_planner.record['wall_seconds']

        def run(self, task='', **kwargs):
            if guidance_text is not None:
                kwargs = kwargs | {'guide': guidance_text}
            if self_planner is not None:
                kwargs = kwargs | {'selfplan': self_planner.text or '(The planning step returned no plan.)'}
            return super().run(task, **kwargs)

        def execute_actions(self, message):
            observations = super().execute_actions(message)
            if diagnosis is not None and diagnosis.pending is not None:
                # Condition E: the public-test observation is already in the history; the diagnosis follows it
                # in the SAME conversation, before the next model query. Nothing is reset.
                observations = observations + (diagnosis.deliver(self) or [])
            return observations

    class JudgedEnvironment(runtime.Environment):
        def __init__(self, *args, **kwargs):
            if diagnosis is not None and isinstance(kwargs.get('container_timeout'), str):
                # The sandbox container's lifetime ("sleep N") must outlast the suspended local deadline. This is a
                # container lifetime only; the agent's local budgets are unchanged.
                seconds = int(kwargs['container_timeout'].rstrip('s'))
                kwargs['container_timeout'] = f'{seconds + int(diagnosis.max_wait_seconds) + 30}s'
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
            attempts.append({'seq': len(attempts) + 1, 'time': utc_now(), 'result': result, 'delivered': True,
                             'action': self.budget.actions, 'source_sha256': digest})
            self.last_candidate = source
            if result.get('status') == 'infrastructure_error' or result.get('task_id') != task_id \
                    or result.get('suite') != 'public':
                attempts[-1]['delivered'] = False
                self.evidence.append({'command': command, 'action': self.budget.actions, 'source_sha256': digest,
                                      'judge_infrastructure_error': result.get('error') or result.get('status')})
                if diagnosis is not None:
                    diagnosis.observe_infrastructure_error(action=self.budget.actions,
                                                           error=result.get('error') or result.get('status'))
                raise v3.limits('InfrastructureError')
            returncode = 0 if result['status'] == 'pass' else 1
            output = {'output': result.get('report', ''), 'returncode': returncode, 'exception_info': ''}
            self.evidence.append({'command': command, 'action': self.budget.actions,
                                  'elapsed_seconds': time.monotonic() - started, 'source_sha256': digest,
                                  'recognized_public_test': True, 'public_status': result['status'],
                                  'judge': {k: result.get(k) for k in ('status', 'passed', 'total', 'verdict_counts',
                                                                       'code_sha256', 'tests_sha256', 'judge_version')},
                                  **output})
            self.budget.tested(digest, returncode)
            if diagnosis is not None:
                diagnosis.on_public_result(result=result, source=source, digest=digest, budget=self.budget,
                                           deadline=self.deadline)
            return output

    return GuidedAgent, JudgedEnvironment


def bound_run(base_function, agent_cls, env_cls, extra_globals=None):
    bindings = dict(base_function.__globals__) | {'Agent': agent_cls, 'Environment': env_cls} | (extra_globals or {})
    function = types.FunctionType(base_function.__code__, bindings, base_function.__name__,
                                  base_function.__defaults__, base_function.__closure__)
    function.__kwdefaults__ = base_function.__kwdefaults__
    return function
