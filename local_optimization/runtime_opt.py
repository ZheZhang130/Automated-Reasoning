"""Versioned minimal extensions around the immutable v3 sandbox and upstream agent."""
import argparse
import json
import logging
import re
import subprocess
import time
import uuid
from pathlib import Path

from optlib import BASELINE, DATA, ENDPOINT, MODEL, ROOT, GPU_LOCK, Lock, digest, on_e, read, save
from transport import NativeHistory, native_messages, is_timeout
from command_transport import execute_stdin_script
import copy
import threading
import runner as v3
import probe as v3model
import litellm
import requests
from litellm.integrations.custom_logger import CustomLogger
from minisweagent.agents.default import DefaultAgent
from minisweagent.exceptions import InterruptAgentFlow
from minisweagent.models.litellm_model import LitellmModel
from minisweagent.models.litellm_textbased_model import LitellmTextbasedModel

TEST_PATTERN = re.compile(r'^\s*python(?:3)?\s+(?:-I\s+)?/public/check\.py(?:\s*<\s*[^;&|\s]+)?(?:\s+2>&1)?\s*$')
PROMPT = """You are an autonomous Python coding agent operating a Linux workspace.
Solve the user's programming task and save the complete Python source at /workspace/solution.py.
Honor its required interface: either a stdin/stdout program or the supplied class and method.
Work on the task yourself. Execute one current action and wait for its result.
Use noninteractive shell commands. Each response contains exactly ONE fenced command:
```mswea_bash_command
pwd
```
Use literal heredocs to write multiline source. Here is the file-writing syntax (replace the placeholder with your own complete program):
```mswea_bash_command
cat > /workspace/solution.py <<'PY'
# Your complete Python source goes here.
PY
```
Return just the ONE current command block, including its closing fence. Do not emit a list of future actions.
Run public tests with the separate command: python -I /public/check.py
Read actual feedback and revise your program when needed. Files persist; shell state does not.
Once your source is saved and you have tested it, submit with the separate command:
echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT
"""
FORMAT_ERROR = """Rejected: {{error}}. No action from that response ran.
Return ONE complete command block with a closing fence. Use a literal heredoc for multiline files.
```mswea_bash_command
pwd
```
{% if finish_reason == 'length' %}The generation limit was reached. Be concise and write the program in smaller complete edits.{% endif %}"""
NATIVE_PROMPT = """You are an autonomous Python coding agent operating a Linux workspace.
Solve the user's task and save complete Python source at /workspace/solution.py, honoring the required stdin/stdout or class/method interface.
Every response must call the native bash tool exactly once, with the current shell command in its command argument. Wait for its output before your next action.
Make changes yourself using noninteractive commands. Use a literal heredoc for multiline source; for example the command argument can contain:
cat > /workspace/solution.py <<'PY'
# Your complete Python source goes here.
PY
Run public tests with the separate command python -I /public/check.py and revise your code using actual feedback.
After saving and testing the source, finish by calling bash with the separate command echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT.
"""


def api(port, route, payload=None, timeout=15):
    url = f'http://127.0.0.1:{port}' + route
    response = requests.get(url, timeout=timeout) if payload is None else requests.post(url, json=payload, timeout=timeout)
    if response.status_code != 200:
        raise RuntimeError(f'Ollama HTTP {response.status_code}: {response.text[:3000]}')
    return response.json()


def exclusive_gpu():
    # Do not unload or stop a user's separate Ollama workload.
    if api(11434, '/api/ps')['models']:
        raise RuntimeError('ForeignModelLoaded: app endpoint has loaded models; waiting is required')
    v3model.unload_project_models()
    deadline = time.monotonic() + 20
    while api(11435, '/api/ps')['models']:
        if time.monotonic() >= deadline:
            raise RuntimeError('Project models did not finish unloading')
        time.sleep(0.2)


class RawCapture(CustomLogger):
    def __init__(self, path):
        super().__init__()
        self.path, self.responses = path, []
        self.requests = []

    def log_pre_api_call(self, model, messages, kwargs):
        payload = kwargs.get('additional_args', {}).get('complete_input_dict')
        if isinstance(payload, dict):
            self.requests.append(payload)
            save(self.path.with_name('ollama-requests.json'), self.requests)

    def log_post_api_call(self, kwargs, response_obj, start_time, end_time):
        raw = kwargs.get('original_response')
        if isinstance(raw, str):
            try:
                obj = json.loads(raw)
            except ValueError:
                return
            self.responses.append(obj)
            save(self.path, self.responses)


class CompletionReason:
    """LiteLLM 1.81.16 drops Ollama's done_reason; preserve it for format feedback."""
    def _query(self, messages, **kwargs):
        before = len(self.capture.responses)
        response = super()._query(messages, **kwargs)
        if len(self.capture.responses) > before and self.capture.responses[-1].get('done_reason') == 'length':
            response.choices[0].finish_reason = 'length'
        return response


class TextModel(CompletionReason, LitellmTextbasedModel):
    pass


class NativeModel(CompletionReason, LitellmModel):
    pass


class FixedNativeModel(NativeHistory, NativeModel):
    pass


class GpuSampler:
    def __init__(self):
        self.samples = []
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.sample, daemon=True)

    def sample(self):
        while not self.stop.is_set():
            result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu,power.draw', '--format=csv,noheader,nounits'], capture_output=True, text=True)
            self.samples.append({'time': time.time(), 'values': result.stdout.strip()})
            self.stop.wait(2)


class Environment(v3.TaskEnvironment):
    def _check_finished(self, output):
        lines = output.get('output', '').lstrip().splitlines()
        if lines and lines[0].strip() == 'COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT' and output['returncode'] == 0:
            if not self.snapshot():
                output.update(output='Submission rejected: /workspace/solution.py is missing or empty. Write the program first.', returncode=1)
                return
        return super()._check_finished(output)

    def execute(self, action, cwd='', *, timeout=None):
        if getattr(self,'stream_large_commands',False) and isinstance(action.get('command'),str) and len(action['command'])>12000:
            output=execute_stdin_script(self,action,cwd,timeout,super().execute)
        else:
            output = super().execute(action, cwd, timeout=timeout)
        event = self.evidence[-1]
        if TEST_PATTERN.fullmatch(action['command']) and not event.get('recognized_public_test'):
            self.budget.tested(event['source_sha256'], output['returncode'])
            event['recognized_public_test'] = True
        if event.get('recognized_public_test'):
            event['public_status'] = 'pass' if output['returncode'] == 0 else 'candidate_failure'
        return output


class Agent(DefaultAgent):
    def query(self):
        if self.env.budget.actions >= self.env.budget.action_limit:
            raise v3.limits('ActionLimit')
        remaining = self.env.deadline - time.monotonic()
        if remaining <= 0:
            raise v3.limits('Deadline')
        self.model.config.model_kwargs['timeout'] = min(self.query_seconds, remaining)
        return super().query()


def run(task_dir, output, model_name, profile_name, *, seed=2108, actions=20, repairs=3, seconds=600):
    output = on_e(output)
    output.mkdir(parents=True, exist_ok=False)
    profile = read(ROOT / 'profiles.json')[profile_name]
    if model_name != MODEL:
        raise ValueError('Unapproved model')
    record = {'run_id': output.name, 'model': model_name, 'condition': 'A', 'profile': profile_name,
              'runtime_version': 'optimization-v4-long-command-transport',
              'profile_config': profile, 'seed': seed, 'action_limit': actions, 'repair_limit': repairs,
              'time_limit_seconds': seconds, 'events': [], 'status': 'InfrastructureError'}
    budget = v3.Budget(actions, repairs)
    env = agent = None
    capture = RawCapture(output / 'ollama-responses.json')
    litellm.callbacks = [capture]
    started = time.monotonic()
    gpu_sampler = GpuSampler()
    gpu_sampler.thread.start()
    server_log = Path('E:/CSC2108Local/logs/ollama-project.stderr.log')
    log_offset = server_log.stat().st_size
    record['implementation_sha256'] = {p.name: digest(p) for p in (ROOT / 'runtime_opt.py', ROOT / 'transport.py', ROOT / 'command_transport.py', ROOT / 'profiles.json', BASELINE / 'runner.py')}
    try:
        task_dir = Path(task_dir).resolve(strict=True)
        allowed = {'task.json', 'public_tests.json', 'check.py', 'solution.py'}
        if any(p.is_symlink() or not p.is_file() or p.name not in allowed for p in task_dir.iterdir()):
            raise ValueError('Unexpected public bundle contents')
        task = read(task_dir / 'task.json')
        if set(task) != {'task_id', 'version', 'statement', 'submission_path'} or task['submission_path'] != 'solution.py':
            raise ValueError('Invalid public task schema')
        record.update(task_id=task['task_id'], task_version=task['version'],
                      public_sha256={p.name: digest(p) for p in task_dir.iterdir()})
        record['isolation'] = v3.isolation_preflight(v3.IMAGE, Path('E:/DockerDesktop'))
        exclusive_gpu()
        record['model_metadata'] = api(11435, '/api/show', {'model': model_name})
        record['tags'] = api(11435, '/api/tags')
        record['gpu_before'] = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu', '--format=csv,noheader'], capture_output=True, text=True).stdout
        cls = (FixedNativeModel if profile.get('native_history') == 'fixed' else NativeModel) if profile['protocol'] == 'native' else TextModel
        kwargs = {'api_base': ENDPOINT, 'num_ctx': profile['context'], 'num_predict': profile['output_tokens'],
                  'temperature': profile.get('temperature', 0.0), 'seed': seed, 'num_retries': 0, 'timeout': 180, 'keep_alive': '10m'}
        if profile.get('sampler'):
            # Direct options avoid LiteLLM's OpenAI frequency->repeat alias and
            # its unsupported presence_penalty parameter filtering.
            kwargs['extra_body'] = {'options': profile['sampler'] | {
                'num_ctx': profile['context'], 'num_predict': profile['output_tokens'],
                'temperature': profile.get('temperature', 0.0), 'seed': seed}}
        if model_name.startswith('qwen3.5'):
            kwargs['think'] = profile['thinking']
        config = dict(model_name='ollama_chat/' + model_name, model_kwargs=kwargs, cost_tracking='ignore_errors',
                      observation_template='<returncode>{{output.returncode}}</returncode>\n{{output.output[:6000]}}',
                      format_error_template=FORMAT_ERROR if profile['protocol'] == 'text' else '{{error}}. Call the native bash tool once with a command argument; wait for output.')
        if profile['protocol'] == 'text':
            config['action_regex'] = r'```(?:mswea_bash_command|bash)\s*\n(.*?)\n```'
        model = cls(**config)
        model.capture = capture
        model.retain_thinking = profile.get('retain_thinking', True)
        env = Environment(budget=budget, deadline=started + seconds, evidence=record['events'], image=v3.IMAGE,
                          cwd='/workspace', run_args=v3.container_args(task_dir) + ['--label', 'csc2108.eval-v2.run=' + output.name], container_timeout=str(seconds + 60) + 's',
                          env={'PYTHONDONTWRITEBYTECODE': '1', 'HOME': '/tmp'})
        save(output / 'container.json', {'container_id': env.container_id, 'run_id': output.name})
        env.stream_large_commands=profile.get('stream_large_commands',False)
        if (task_dir / 'solution.py').exists():
            v3.docker('exec', env.container_id, 'cp', '/public/solution.py', '/workspace/solution.py')
        prompt = PROMPT if profile['protocol'] == 'text' else NATIVE_PROMPT
        agent = Agent(model, env, system_template=prompt, instance_template='{{task}}', step_limit=actions + 8,
                      cost_limit=0, wall_time_limit_seconds=seconds, output_path=output / 'trajectory.json')
        agent.query_seconds = profile.get('query_seconds', 180)
        save(output / 'task.json', task)
        save(output / 'configuration.json', agent.serialize())
        result = agent.run(task['statement'])
        record['status'] = result.get('exit_status', 'Unknown')
    except Exception as exc:
        record.update(error_type=type(exc).__name__, error=str(exc))
        if is_timeout(exc):
            # A declared query/wall budget expiration is a task outcome, not a
            # fabricated complete response or a reason to erase the attempt.
            record['status'] = 'ModelTimeout'
    finally:
        record.update(elapsed_seconds=time.monotonic() - started, actions=budget.actions,
                      repairs=min(repairs, budget.repairs), repair_events=budget.events)
        gpu_sampler.stop.set()
        gpu_sampler.thread.join(timeout=5)
        save(output / 'gpu-samples.json', gpu_sampler.samples)
        if env:
            candidate = env.last_candidate
            if candidate is None and env.container_id:
                try:
                    candidate = env.snapshot()
                except Exception as exc:
                    record['extraction_error'] = str(exc)
            if candidate is not None:
                (output / 'solution.py').write_bytes(candidate)
                record['submission_sha256'] = digest(output / 'solution.py')
            env.cleanup()
        if agent:
            agent.save(output / 'trajectory.json')
            record['format_errors'] = sum(m.get('extra', {}).get('interrupt_type') == 'FormatError' for m in agent.messages)
        record['public_tests'] = [e for e in record['events'] if e.get('recognized_public_test')]
        record['gpu_after'] = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu', '--format=csv,noheader'], capture_output=True, text=True).stdout
        try:
            record['ollama_ps'] = api(11435, '/api/ps')
        except Exception as exc:
            record['telemetry_error'] = str(exc)
        raw = capture.responses
        record['model_calls'] = agent.n_calls if agent else 0
        record['token_telemetry_complete'] = len(raw) == record['model_calls']
        record['unobserved_model_calls'] = max(0, record['model_calls'] - len(raw))
        record['unobserved_output_token_upper_bound'] = record['unobserved_model_calls'] * profile['output_tokens']
        record['wire_requests_captured'] = len(capture.requests)
        if profile.get('native_history') == 'fixed':
            # Every non-initial native request must preserve all prior executed
            # assistant calls and their tool results, in original order.
            record['native_history_wire_verified'] = all(
                all(m.get('tool_name') == 'bash' for m in r.get('messages', []) if m['role'] == 'tool') and
                sum(len(m.get('tool_calls') or []) for m in r.get('messages', [])) == sum(m['role'] == 'tool' for m in r.get('messages', []))
                for r in capture.requests)
        if profile.get('sampler'):
            expected_options = profile['sampler'] | {'num_ctx': profile['context'], 'num_predict': profile['output_tokens'],
                                                   'temperature': profile.get('temperature', 0.0), 'seed': seed}
            record['sampler_wire_verified'] = (len(capture.requests) == record['model_calls'] and
                all(r.get('options') == expected_options for r in capture.requests))
        record['inference'] = {'calls_captured': len(raw),
                               **{key: sum(r.get(key, 0) for r in raw) for key in ('prompt_eval_count', 'eval_count', 'prompt_eval_duration', 'eval_duration', 'load_duration')},
                               'done_reasons': [r.get('done_reason') for r in raw],
                               'maximum_prompt_tokens': max([r.get('prompt_eval_count', 0) for r in raw] + [0])}
        with server_log.open('rb') as source:
            source.seek(log_offset)
            log = source.read().decode('utf-8', errors='replace')
        (output / 'ollama-server.log').write_text(log, encoding='utf-8')
        record['context_events'] = [line for line in log.splitlines() if re.search(r'truncating|truncated = [1-9]', line)]
        save(output / 'result.json', record)
        litellm.callbacks = []
    return record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--task', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--model', choices=[MODEL], default=MODEL)
    p.add_argument('--profile', choices=list(read(ROOT / 'profiles.json')), default='heredoc-v6-16k-common')
    p.add_argument('--seconds', type=int, default=600)
    p.add_argument('--actions', type=int, default=20)
    p.add_argument('--repairs', type=int, default=3)
    p.add_argument('--seed', type=int, default=2108)
    args = p.parse_args()
    if not 1 <= args.seconds <= 1200 or not 1 <= args.actions <= 60 or not 0 <= args.repairs <= 10:
        p.error('Invalid execution budget')
    if '-v4-' in args.profile and (DATA / 'HOLD_V4').exists():
        raise RuntimeError('Exploratory v4 schedule held; preserve its evidence and use frozen v5 development')
    logging.getLogger('minisweagent.environment').setLevel(logging.WARNING)
    with Lock(GPU_LOCK):
        result = run(args.task, args.output, args.model, args.profile, seed=args.seed, actions=args.actions, repairs=args.repairs, seconds=args.seconds)
    print(json.dumps({k: result.get(k) for k in ('run_id', 'task_id', 'model', 'profile', 'status', 'elapsed_seconds', 'actions', 'repairs', 'format_errors', 'inference')}), flush=True)


if __name__ == '__main__':
    main()
