"""No-inference sandbox and official evaluator controls using existing synthetic fixtures."""
import argparse
import json
import sys
import time
from pathlib import Path

from .cli import REPO, ROOT, VENDOR, fresh_output, save, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    metadata = verify(evaluator=True)
    out = fresh_output(args.output)
    sys.path.insert(0, str(REPO / 'local_eval_v2'))
    import runtime
    sys.path.insert(0, str(REPO / 'local_optimization'))
    from judge_watch import score
    from minisweagent.exceptions import InterruptAgentFlow
    import litellm

    public = ROOT / 'eval-v2/development-v5/public/dev-negative-squares'
    private = ROOT / 'eval-v2/development-v5/private/dev-negative-squares.json'
    # Reuse the existing Qwen-authored synthetic positive control, never a benchmark candidate.
    positive = ROOT / 'optimization/diagnostics/dev-negative-squares--native-fixed-16k-4k/solution.py'
    events = []
    budget = runtime.v3.Budget(20, 3)
    runtime.v3.isolation_preflight(runtime.v3.IMAGE, Path('E:/DockerDesktop'))
    env = runtime.Environment(budget=budget, deadline=time.monotonic() + 90, evidence=events,
          image=runtime.v3.IMAGE, cwd='/workspace', run_args=runtime.v3.container_args(public),
          container_timeout='100s', env={'HOME': '/tmp', 'PYTHONDONTWRITEBYTECODE': '1'})
    controls = {}
    try:
        inspection = json.loads(runtime.v3.docker('inspect', env.container_id).stdout)[0]
        h = inspection['HostConfig']
        assert h['NetworkMode'] == 'none' and h['ReadonlyRootfs'] and not h['Privileged']
        assert h['Memory'] == h['MemorySwap'] == 512 * 1024**2 and h['PidsLimit'] == 64
        assert h['NanoCpus'] == 10**9 and inspection['Config']['User'] == '65534:65534'
        assert 'ALL' in h['CapDrop'] and any('no-new-privileges' in x for x in h['SecurityOpt'])
        mounts = [m for m in inspection['Mounts'] if m['Type'] == 'bind']
        assert len(mounts) == 1 and mounts[0]['Destination'] == '/public' and not mounts[0]['RW']
        controls['isolation'] = True
        model = runtime.TextModel(model_name='ollama_chat/qwen3.5:9b', cost_tracking='ignore_errors',
              action_regex=r'```(?:mswea_bash_command|bash)\s*\n(.*?)\n```', format_error_template=runtime.FORMAT_ERROR)
        rejected = False
        try:
            model._parse_actions(litellm.ModelResponse(choices=[{'message': {'role': 'assistant',
                'content': '```mswea_bash_command\ntouch /workspace/SHOULD_NOT_EXIST'}, 'finish_reason': 'length'}]))
        except InterruptAgentFlow:
            rejected = True
        assert rejected
        env.execute({'command': "cat > /workspace/solution.py <<'PY'\nprint(0)\nPY"})
        failed = env.execute({'command': 'python -I /public/check.py'})
        assert failed['returncode'] != 0 and events[-1]['recognized_public_test']
        env.execute({'command': "cat > /workspace/solution.py <<'PY'\n" + positive.read_text(encoding='utf-8') + '\nPY'})
        passed = env.execute({'command': 'python -I /public/check.py'})
        assert passed['returncode'] == 0 and budget.repairs == 1
        assert env.execute({'command': 'test ! -e /workspace/SHOULD_NOT_EXIST'})['returncode'] == 0
        submitted = False
        try:
            env.execute({'command': 'echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT'})
        except InterruptAgentFlow:
            submitted = True
        assert submitted
        controls.update(malformed_action_rejected=True, persistent_real_shell=True,
                        public_failure_changed_repair_pass=True, repairs=budget.repairs, submission=True)
    finally:
        env.cleanup()
        save(out / 'sandbox-events.json', events)
    # Deliberately wrong/syntax/resource-only fixtures, never benchmark solutions.
    for label, source, expected in (
        ('positive', positive.read_text(encoding='utf-8'), 'pass'),
        ('wrong', 'print(0)\n', 'candidate_failure'),
        ('syntax', 'def broken(\n', 'candidate_failure'),
        ('oom', 'payload = bytearray(2 * 1024 ** 3)\n', 'candidate_resource_failure')):
        folder = out / label
        folder.mkdir()
        (folder / 'solution.py').write_text(source, encoding='utf-8')
        evaluation = score(folder, private, VENDOR, 'csc2108-lcb-judge:v2')
        save(folder / 'evaluation.json', evaluation)
        assert evaluation['status'] == expected, (label, evaluation)
        controls['judge_' + label] = evaluation['status']
    save(out / 'checks.json', {'status': 'pass', 'model_calls': 0, 'checks': controls, 'identity': metadata})
    print(json.dumps({'status': 'pass', 'output': str(out), 'checks': controls}))


if __name__ == '__main__':
    main()
