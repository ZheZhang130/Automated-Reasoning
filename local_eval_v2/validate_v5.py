"""Validate new public interfaces and submission/test hooks, outside measured tasks."""
import base64
import unittest
from pathlib import Path

from common import DATA, save
from runtime import Environment, TEST_PATTERN
import runner as v3
from pilot import score
from minisweagent.exceptions import Submitted


class Hooks(unittest.TestCase):
    def test_common_public_command_spellings(self):
        for command in ('python -I /public/check.py', 'python3 /public/check.py', 'python -I /public/check.py < input.txt'):
            self.assertTrue(TEST_PATTERN.fullmatch(command))
        for command in ('cat /public/check.py', 'echo python /public/check.py', 'python /other/check.py'):
            self.assertFalse(TEST_PATTERN.fullmatch(command))

    def test_missing_submission_does_not_exit(self):
        env = Environment.__new__(Environment)
        env.container_id = None
        env.snapshot = lambda: None
        output = {'output': 'COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT\n', 'returncode': 0}
        env._check_finished(output)
        self.assertEqual(output['returncode'], 1)
        self.assertIn('missing', output['output'])

    def test_existing_submission_uses_upstream_termination(self):
        env = Environment.__new__(Environment)
        env.container_id = None
        env.snapshot = lambda: b'# existing candidate'
        with self.assertRaises(Submitted):
            env._check_finished({'output': 'COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT\n', 'returncode': 0})


def interfaces():
    root = DATA / 'audit/interfaces-v5'
    root.mkdir(parents=True, exist_ok=False)
    public = DATA / 'development-v5/public/dev-functional-distinct'
    results = []
    for label, code, expected in [('correct', 'class Solution:\n    def countDistinct(self, values: List[int]) -> int:\n        return len(set(values))\n', 'pass'),
                                   ('wrong', 'class Solution:\n    def countDistinct(self, values):\n        return 0\n', 'candidate_failure')]:
        run = root / label
        run.mkdir()
        (run / 'solution.py').write_text(code, encoding='utf-8')
        script = "import base64,pathlib,sys,subprocess; pathlib.Path('/workspace/solution.py').write_bytes(base64.b64decode(sys.stdin.read())); r=subprocess.run(['python','-I','/public/check.py']); sys.exit(r.returncode)"
        try:
            result = v3.docker('run', '-i', *v3.container_args(public), v3.IMAGE, 'python', '-I', '-c', script,
                               input=base64.b64encode(code.encode()).decode(), timeout=30)
            public_status = 'pass'
        except __import__('subprocess').CalledProcessError as exc:
            result = exc
            public_status = 'candidate_failure'
        official = score(run, DATA / 'development-v5/private/dev-functional-distinct.json',
                         Path('E:/CSC2108Local/vendor/LiveCodeBench'), 'csc2108-lcb-judge:v1')
        results.append({'label': label, 'expected': expected, 'public': public_status, 'official': official})
        save(root / 'result.json', results)
        assert public_status == official['status'] == expected
        print({'interface': 'functional', 'fixture': label, 'public': public_status, 'official': official['status']})


if __name__ == '__main__':
    unittest.main(exit=False, verbosity=2)
    interfaces()
