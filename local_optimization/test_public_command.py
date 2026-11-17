"""A common harmless stderr redirect must not bypass repair accounting."""
import unittest
from runtime_opt import TEST_PATTERN


class PublicCommand(unittest.TestCase):
    def test_direct_checks(self):
        for command in ['python -I /public/check.py', 'python3 /public/check.py < /tmp/input',
                        'python -I /public/check.py 2>&1', 'python /public/check.py < /tmp/input 2>&1']:
            self.assertIsNotNone(TEST_PATTERN.fullmatch(command), command)

    def test_nonchecks_and_masked_exit_status(self):
        for command in ['cat /public/check.py', 'python -c "print(\'/public/check.py\')"',
                        'python /public/check.py || true', 'python /public/check.py; echo ok',
                        'echo python /public/check.py', 'python /public/check.py < x; pwd']:
            self.assertIsNone(TEST_PATTERN.fullmatch(command), command)


if __name__ == '__main__':
    unittest.main(verbosity=2)
