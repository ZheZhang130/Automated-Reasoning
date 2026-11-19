"""Portable synthetic fixtures and Docker controls; no LLM calls."""
import argparse
import json
import sys
import time
from pathlib import Path

from .platform_support import REPO, Settings


def fixtures(output, settings):
    from .cli import save
    root = settings.output(output)
    public = root / 'public'
    public.mkdir()
    cases = [{'input': '2 -5\n', 'output': '-3\n', 'testtype': 'stdin'},
             {'input': '-9 -11\n', 'output': '-20\n', 'testtype': 'stdin'}]
    save(public / 'task.json', {'task_id': 'portable-synthetic-sum', 'version': '1',
         'statement': 'Read two signed integers from stdin and print their sum. Save solution.py, run the public tests, and submit.',
         'submission_path': 'solution.py'})
    save(public / 'public_tests.json', cases[:1])
    (public / 'check.py').write_bytes((REPO / 'local_eval_v2/public_check.py').read_bytes())
    (public / 'solution.py').write_text('print(0)\n', encoding='utf-8')
    save(root / 'private.json', {'public_test_cases': json.dumps(cases[:1]),
                               'private_test_cases': json.dumps(cases[1:]), 'metadata': '{}'})
    return {'public': str(public), 'private_row': str(root / 'private.json')}


def main():
    from .cli import save, verify
    from .portable import load_runtime, verify_images
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    settings = Settings.load('portable')
    identity = verify(services=False, evaluator=True, settings=settings)
    images = verify_images(settings)
    out = settings.output(args.output)
    bundle = fixtures(out / 'fixture', settings)
    runtime = load_runtime(settings)
    events = []
    budget = runtime.v3.Budget(20, 3)
    env = runtime.Environment(budget=budget, deadline=time.monotonic() + 90, evidence=events,
          image=images['agent']['reference'], cwd='/workspace',
          run_args=runtime.v3.container_args(Path(bundle['public'])), container_timeout='100s',
          env={'HOME': '/tmp', 'PYTHONDONTWRITEBYTECODE': '1'})
    from minisweagent.exceptions import InterruptAgentFlow
    try:
        info = json.loads(runtime.v3.docker('inspect', env.container_id).stdout)[0]
        host = info['HostConfig']
        assert host['NetworkMode'] == 'none' and host['ReadonlyRootfs'] and not host['Privileged']
        assert host['Memory'] == host['MemorySwap'] == 512 * 1024**2 and host['PidsLimit'] == 64
        assert host['NanoCpus'] == 10**9 and info['Config']['User'] == '65534:65534'
        assert 'ALL' in host['CapDrop'] and any('no-new-privileges' in x for x in host['SecurityOpt'])
        mounts = [m for m in info['Mounts'] if m['Type'] == 'bind']
        assert len(mounts) == 1 and mounts[0]['Destination'] == '/public' and not mounts[0]['RW']
        env.execute({'command': "cat > /workspace/solution.py <<'PY'\nprint(0)\nPY"})
        assert env.execute({'command': 'python -I /public/check.py'})['returncode'] != 0
        source = 'import sys\nprint(sum(map(int, sys.stdin.read().split())))\n'  # Trusted synthetic arithmetic only.
        env.execute({'command': "cat > /workspace/solution.py <<'PY'\n" + source + 'PY'})
        assert env.execute({'command': 'python -I /public/check.py'})['returncode'] == 0
        assert budget.repairs == 1
        submitted = False
        try:
            env.execute({'command': 'echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT'})
        except InterruptAgentFlow:
            submitted = True
        assert submitted and env.last_candidate == source.encode()
    finally:
        env.cleanup()
        save(out / 'events.json', events)
    sys.path.insert(0, str(REPO / 'local_optimization'))
    from judge_watch import score
    outcomes = {}
    for label, code, expected in [('positive', source, 'pass'), ('wrong', 'print(0)\n', 'candidate_failure')]:
        run = out / label
        run.mkdir()
        (run / 'solution.py').write_text(code, encoding='utf-8')
        evaluation = score(run, Path(bundle['private_row']), settings.vendor, images['judge']['reference'])
        save(run / 'evaluation.json', evaluation)
        assert evaluation['status'] == expected, evaluation
        outcomes[label] = evaluation['status']
    save(out / 'checks.json', {'status': 'pass', 'model_calls': 0, 'identity': identity, 'images': images,
         'isolation': 'verified', 'changed_repair_groups': budget.repairs, 'submission': True, 'independent_evaluator': outcomes})
    print(json.dumps({'status': 'pass', 'output': str(out), 'model_calls': 0}))


if __name__ == '__main__':
    main()
