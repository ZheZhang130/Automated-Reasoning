"""Integration boundary checks without model inference or candidate execution."""
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from local_agent import cli


class Interface(unittest.TestCase):
    def test_exact_frozen_identity_and_prompt(self):
        result = cli.verify(services=False)
        self.assertEqual(result['frozen_files_verified'], 38)
        self.assertEqual(result['system_prompt_sha256'],
                         '291f0f67e2dd461f777f9798a08c99de14d987b99acb6bc4e5f213162590ef05')
        self.assertEqual(result['budgets'], {'actions': 20, 'repair_groups': 3,
                                           'task_seconds': 600, 'request_seconds': 180})

    def test_changed_source_fails_instead_of_skipping_integrity_check(self):
        real = cli.digest
        def changed(path):
            return 'changed' if str(path).endswith('runner.py') else real(path)
        with patch.object(cli, 'digest', side_effect=changed), self.assertRaisesRegex(RuntimeError, 'Frozen source changed'):
            cli.verify(services=False)

    def test_no_candidate_and_partial_telemetry_remain_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            (out / 'runtime').mkdir()
            cli.save(out / 'runtime/result.json', {'status': 'Deadline', 'model_calls': 3,
                     'inference': {'calls_captured': 2, 'eval_count': 8192, 'eval_duration': 2_000_000_000}})
            result = cli.envelope(out, {'model': cli.MODEL, 'profile': cli.PROFILE},
                                  subprocess.CompletedProcess([], 0), time.monotonic())
            self.assertIsNone(result['candidate_path'])
            self.assertIsNone(result['trajectory_path'])
            self.assertEqual(result['termination_reason'], 'Deadline')
            self.assertEqual(result['usage']['observed_generated_tokens'], 8192)
            self.assertEqual(result['usage']['unobserved_generated_tokens_upper_bound'], 4096)
            self.assertFalse(result['usage']['token_telemetry_complete'])
            self.assertEqual(result['timings']['eval_duration_seconds'], 2)

    def test_checkout_is_never_a_runtime_artifact_destination(self):
        with self.assertRaisesRegex(ValueError, 'outside the checkout'):
            cli.fresh_output(cli.REPO / 'should-not-be-created')
        self.assertFalse((cli.REPO / 'should-not-be-created').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
