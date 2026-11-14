"""Judge tests. Unit tests need no Docker; container tests are skipped without
Docker or the csc2108-judge image. Run from judge/:

    python -m unittest discover -s tests
"""
import json
import subprocess
import sys
import tarfile
import io
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

EVAL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EVAL))
sys.path.insert(0, str(EVAL / "container"))

import judge as J  # noqa: E402  (container/judge.py)
from judgekit import IMAGE, Judge, JudgeError, docker_bin  # noqa: E402

FIXTURES = EVAL / "tests" / "fixtures"     # tasks/ and hidden/ in the same layout as judge/
TASK = "fixture-sum-signed"
OTHER = "fixture-max"
CORRECT = "a, b = map(int, input().split())\nprint(a + b)\n"


class ComparisonTest(unittest.TestCase):
    def test_lcb_comparison(self):
        self.assertTrue(J.outputs_match("1 2\n3\n", "1 2\n3"))
        self.assertTrue(J.outputs_match("  1 2  \n 3", "1 2\n3\n\n"))
        self.assertTrue(J.outputs_match("1.50", "1.5"))
        self.assertFalse(J.outputs_match("1\n2", "1 2"))
        self.assertFalse(J.outputs_match("Yes", "yes"))
        self.assertFalse(J.outputs_match("0.333333", "0.3333333"))

    def test_archive_member_names(self):
        self.assertEqual(J._safe_member("t1/01.in"), ("t1", "01.in"))
        self.assertEqual(J._safe_member("t1/task.json"), ("t1", "task.json"))
        for bad in ("../x/01.in", "t1/../01.in", "t1/sub/01.in", ".hidden/01.in",
                    "t1/run.sh", "01.in"):
            self.assertIsNone(J._safe_member(bad), bad)

    def test_report_is_built_from_result_fields(self):
        first = {"name": "02", "verdict": "WA", "input": "in", "expected": "5", "actual": "3"}
        report = J.format_report("public", 1, 2, first)
        self.assertTrue(report.startswith("PUBLIC TESTS: 1/2 passed"))
        for text in ("case 02: WA", "--- input ---", "--- expected ---", "--- actual ---"):
            self.assertIn(text, report)
        self.assertEqual(J.format_report("public", 2, 2, None), "PUBLIC TESTS: 2/2 passed")


def _docker_ready():
    try:
        docker = docker_bin()
        return subprocess.run([docker, "image", "inspect", IMAGE],
                              capture_output=True, timeout=30).returncode == 0
    except (JudgeError, OSError, subprocess.SubprocessError):
        return False


DOCKER = _docker_ready()


@unittest.skipUnless(DOCKER, f"Docker or image {IMAGE} not available")
class PublicJudgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.judge = Judge("public", name="csc2108-judge-test-public", cpus=2, root=FIXTURES)
        cls.info = cls.judge.up(force=True)

    @classmethod
    def tearDownClass(cls):
        cls.judge.down()

    def run_code(self, code, task=TASK, **kwargs):
        return self.judge.run(task, code, **kwargs)

    def test_info(self):
        self.assertEqual(self.info["suite"], "public")
        self.assertEqual(self.info["tasks"], sorted([OTHER, TASK]))
        self.assertEqual(self.info["slots"], 2)

    def test_reuses_running_container(self):
        self.assertEqual(self.judge.up()["loaded_at"], self.info["loaded_at"])

    def test_accepted(self):
        result = self.run_code(CORRECT)
        self.assertEqual(result["status"], "pass")
        self.assertEqual((result["passed"], result["total"]), (2, 2))
        self.assertIsNone(result["first_failure"])
        self.assertEqual(result["code_sha256"], J.sha256_bytes(CORRECT.encode()))
        self.assertEqual(result["report"], "PUBLIC TESTS: 2/2 passed")

    def test_wrong_answer_feedback(self):
        result = self.run_code("input()\nprint(4)\n")
        self.assertEqual(result["status"], "candidate_failure")
        first = result["first_failure"]
        self.assertEqual(first["verdict"], "WA")
        self.assertEqual(first["actual"].strip(), "4")
        self.assertIn("expected", first)
        self.assertIn("--- expected ---", result["report"])

    def test_candidate_verdicts(self):
        for code, verdict, kwargs in (("print(\n", "CE", {}), ("  \n", "MISSING", {}),
                                      ("raise ValueError('boom')\n", "RE", {}),
                                      ("while True: pass\n", "TLE", {"time_limit": 1})):
            with self.subTest(verdict=verdict):
                result = self.run_code(code, **kwargs)
                self.assertEqual(result["status"], "candidate_failure")
                self.assertEqual(result["first_failure"]["verdict"], verdict)
        self.assertIn("ValueError: boom",
                      self.run_code("raise ValueError('boom')\n")["first_failure"]["stderr_tail"])

    def test_unknown_task_is_infrastructure_error(self):
        result = self.run_code(CORRECT, task="no-such-task")
        self.assertEqual(result["status"], "infrastructure_error")
        self.assertIn("unknown task", result["error"])

    def test_submission_cannot_read_tests(self):
        probe = ("import os\nout = []\n"
                 f"for p in ('/var/judge/suite/{TASK}/01.out', '/var/judge/suite.json'):\n"
                 "    try:\n        open(p).read(); out.append('READ')\n"
                 "    except OSError as e:\n        out.append(type(e).__name__)\n"
                 "try:\n    os.listdir('/var/judge'); out.append('LISTED')\n"
                 "except OSError as e:\n    out.append(type(e).__name__)\n"
                 "print(' '.join(out))\n")
        actual = self.run_code(probe)["first_failure"]["actual"]
        self.assertEqual(actual.split(), ["PermissionError"] * 3)

    def test_no_network(self):
        code = ("import socket\ntry:\n    socket.create_connection(('1.1.1.1', 53), timeout=2)\n"
                "    print('CONNECTED')\nexcept OSError:\n    print('blocked')\n")
        self.assertEqual(self.run_code(code)["first_failure"]["actual"].strip(), "blocked")

    def test_nothing_survives_a_call(self):
        spawn = ("import os, subprocess\n"
                 "subprocess.Popen(['sleep', '300'], start_new_session=True)\n"
                 "open(os.path.join(os.environ['TMPDIR'], 'mark'), 'w').write('x')\n"
                 "open('/dev/shm/mark', 'w').write('x')\nprint('spawned')\n")
        self.run_code(spawn)
        check = ("import os\nprint(len(os.listdir(os.environ['TMPDIR'])),"
                 " os.path.exists('/dev/shm/mark'))\n")
        self.assertEqual(self.run_code(check)["first_failure"]["actual"].split(), ["0", "False"])
        docker = docker_bin()
        ps = subprocess.run([docker, "exec", self.judge.name, "python3", "-c",
                             "import os\nprint(sum(1 for p in os.listdir('/proc') if p.isdigit()"
                             " and os.stat('/proc/'+p).st_uid >= 2000))"],
                            capture_output=True, text=True, timeout=30)
        self.assertEqual(ps.stdout.strip(), "0")

    def test_parallel_calls(self):
        with ThreadPoolExecutor(6) as pool:
            results = list(pool.map(lambda _: self.run_code(CORRECT), range(6)))
        self.assertEqual([r["status"] for r in results], ["pass"] * 6)

    def test_selftest(self):
        result = self.judge.selftest()
        self.assertTrue(result["ok"], json.dumps(result["checks"], indent=1))


@unittest.skipUnless(DOCKER, f"Docker or image {IMAGE} not available")
class HiddenJudgeTest(unittest.TestCase):
    def test_same_interface_on_hidden_suite(self):
        judge = Judge("hidden", name="csc2108-judge-test-hidden", cpus=2, root=FIXTURES)
        try:
            info = judge.up(force=True)
            self.assertEqual(info["suite"], "hidden")
            result = judge.run(TASK, CORRECT)
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["total"], 5)
            self.assertTrue(result["report"].startswith("HIDDEN TESTS: 5/5"))
            wrong = judge.run(TASK, "input()\nprint(4)\n")
            self.assertEqual(wrong["status"], "candidate_failure")
        finally:
            judge.down()


if __name__ == "__main__":
    unittest.main()
