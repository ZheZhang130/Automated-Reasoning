"""Meaningful scheduling, resume, budget and interface boundary checks."""
import argparse
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from common import read, save
from batch import Lock, run_batch, schedule
from validate_v5 import Hooks


class Scheduling(unittest.TestCase):
    def test_two_attempts_are_unique_and_model_order_rotates(self):
        jobs = schedule({'tasks': [{'task_id': 'task-a'}, {'task_id': 'task-b'}]}, ['m1', 'm2', 'm3'], 2, 'p')
        self.assertEqual(len(jobs), 12)
        self.assertEqual(len({j['key'] for j in jobs}), 12)
        for model in ('m1', 'm2', 'm3'):
            self.assertEqual([j['seed'] for j in jobs if j['model'] == model], [2108, 2109, 2108, 2109])
        self.assertEqual([j['model'] for j in jobs[:3]], ['m1', 'm2', 'm3'])
        self.assertEqual([j['model'] for j in jobs[3:6]], ['m2', 'm3', 'm1'])

    def test_completed_jobs_resume_without_repeating_inference_or_judging(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            jobs = [{'key': 'first'}, {'key': 'second'}]
            save(root / 'plan.json', {'source_sha256': {}, 'jobs': jobs})
            for job in jobs:
                save(root / 'runs' / job['key'] / 'complete.json', {'sentinel': job['key']})
            before = [(p, p.read_bytes(), p.stat().st_mtime_ns) for p in root.glob('runs/*/complete.json')]
            args = argparse.Namespace(batch=root, resume=True)
            with patch('batch.source_hashes', return_value={}), patch('batch.api') as api, patch('batch.score') as judge, patch('batch.subprocess.Popen') as inference:
                run_batch(args)
                api.assert_not_called()
                judge.assert_not_called()
                inference.assert_not_called()
            for path, content, timestamp in before:
                self.assertEqual(path.read_bytes(), content)
                self.assertEqual(path.stat().st_mtime_ns, timestamp)

    def test_live_batch_lock_is_never_removed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'batch.lock'
            import socket
            save(path, {'pid': 1234, 'host': socket.gethostname()})
            before = path.read_bytes()
            with patch('common.alive', return_value=True), self.assertRaises(RuntimeError):
                with Lock(path):
                    pass
            self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
