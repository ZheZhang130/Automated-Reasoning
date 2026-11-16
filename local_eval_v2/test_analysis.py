"""Known-outcome accounting check for repeated, paired research reporting."""
import tempfile
import unittest
from pathlib import Path

from analyze import analyze
from common import read, save


class Accounting(unittest.TestCase):
    def test_paired_denominators_and_ordered_recovery(self):
        with tempfile.TemporaryDirectory() as folder:
            batch = Path(folder)
            jobs = []
            # A: 3/4 passes, B: 1/4. Two problem clusters, two repetitions each.
            correct = {'a': [1, 1, 1, 0], 'b': [0, 0, 1, 0]}
            for model, values in correct.items():
                for index, value in enumerate(values):
                    key = model + str(index)
                    task = 't' + str(index // 2)
                    job = {'key': key, 'task_id': task, 'model': model, 'repetition': index % 2 + 1}
                    jobs.append(job)
                    attempt = batch / 'attempts' / key
                    # Passing before a failure alone must not count as recovery.
                    tests = [{'returncode': 0}, {'returncode': 1}] if index == 0 else []
                    save(attempt / 'result.json', {'status': 'Submitted', 'elapsed_seconds': 1,
                         'actions': 3, 'repairs': 0, 'public_tests': tests, 'events': []})
                    save(attempt / 'private_evaluation.json', {'status': 'pass' if value else 'candidate_failure'})
                    save(batch / 'runs' / key / 'complete.json', {'attempt': str(attempt)})
            save(batch / 'plan.json', {'models': ['a', 'b'], 'repetitions': 2, 'jobs': jobs,
                 'profile': 'test', 'profile_config': {'temperature': .2},
                 'manifest': {'tasks': [{'task_id': 't0'}, {'task_id': 't1'}]}})
            analyze(batch, batch / 'report.md')
            summary = read(batch / 'analysis.json')
            self.assertEqual((summary['completed'], summary['remaining']), (8, 0))
            self.assertEqual(summary['models']['a']['accuracy_completed'], .75)
            self.assertEqual(summary['models']['b']['accuracy_completed'], .25)
            self.assertEqual(summary['models']['a']['problems_any_pass'], 2)
            self.assertEqual(summary['models']['a']['problems_all_attempts_pass'], 1)
            self.assertEqual(summary['models']['a']['public_recoveries'], 0)
            self.assertEqual(summary['paired'][0]['complete_problem_pairs'], 2)
            self.assertEqual(summary['paired'][0]['accuracy_difference'], .5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
