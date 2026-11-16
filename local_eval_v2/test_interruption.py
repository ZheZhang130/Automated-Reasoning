"""Interrupted attempts must remain explicit and preserve their trajectory."""
import argparse
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from batch import run_batch
from common import digest, save


class Interruption(unittest.TestCase):
    def test_partial_attempt_cannot_silently_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            public = root / 'public'
            public.mkdir()
            private = root / 'private.json'
            save(private, {})
            attempt = root / 'runs' / 'job' / 'attempt-01'
            save(attempt / 'trajectory.json', {'sentinel': 'partial evidence'})
            original = (attempt / 'trajectory.json').read_bytes()
            save(root / 'plan.json', {'source_sha256': {}, 'jobs': [{'key': 'job', 'task_id': 'task', 'model': 'm'}],
                 'tasks': {'task': {'public': str(public), 'private': str(private), 'public_sha256': {},
                                    'private_sha256': digest(private)}}, 'model_digests': {'m': 'digest'}})
            args = argparse.Namespace(batch=root, resume=True, retry_interrupted=False)
            with patch('batch.source_hashes', return_value={}), patch('batch.api', return_value={'models': [{'name': 'm', 'digest': 'digest'}]}), patch('batch.subprocess.Popen') as inference, patch('batch.score') as judge:
                with self.assertRaisesRegex(RuntimeError, 'requires explicit --retry-interrupted'):
                    run_batch(args)
                inference.assert_not_called()
                judge.assert_not_called()
            self.assertEqual((attempt / 'trajectory.json').read_bytes(), original)
            self.assertTrue((attempt / 'interrupted.json').exists())
            self.assertFalse((root / 'runs/job/attempt-02').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
