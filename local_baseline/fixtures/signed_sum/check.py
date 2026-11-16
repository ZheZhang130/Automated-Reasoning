"""Visible development tests; run with python -I /public/check.py."""
import importlib.util
import unittest

spec = importlib.util.spec_from_file_location("candidate", "/workspace/solution.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class SignedSumTests(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(candidate.signed_sum(2, 3), 5)

    def test_negative(self):
        self.assertEqual(candidate.signed_sum(-4, 1), -3)

    def test_zero(self):
        self.assertEqual(candidate.signed_sum(0, 0), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
