"""Unit tests for enhanced_de foundation modules (ledger_guard, static_analyzer, tasks_v2, mutant_pool)."""
import json
import tempfile
import unittest
from pathlib import Path

from enhanced_de import ledger_guard, mutant_pool, static_analyzer, tasks_v2


class TestLedgerGuard(unittest.TestCase):
    def test_init_and_verify_enforces_hard_caps(self):
        with tempfile.TemporaryDirectory() as td:
            lp = Path(td) / 'api-ledger.json'
            with self.assertRaises(RuntimeError):
                ledger_guard.verify_ledger(lp)
            with self.assertRaises(ValueError):
                ledger_guard.init_ledger(lp, max_requests=25, max_usd=10.0)
            with self.assertRaises(ValueError):
                ledger_guard.init_ledger(lp, max_requests=20, max_usd=15.0)
            ledger_guard.init_ledger(lp, max_requests=20, max_usd=10.0)
            info = ledger_guard.verify_ledger(lp)
            self.assertEqual(info['max_requests'], 20)
            self.assertEqual(info['max_usd'], 10.0)
            self.assertEqual(info['requests_used'], 0)
            # Tampered cap above 20 must fail closed
            raw = json.loads(lp.read_text(encoding='utf-8'))
            raw['max_requests'] = 2000
            lp.write_text(json.dumps(raw), encoding='utf-8')
            with self.assertRaises(RuntimeError):
                ledger_guard.verify_ledger(lp)

    def test_audit_codex_events_catches_started_tool_and_malformed(self):
        good = '\n'.join([
            json.dumps({'type': 'thread.started', 'thread_id': 't1'}),
            json.dumps({'type': 'item.started', 'item': {'type': 'reasoning'}}),
            json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message'}}),
            json.dumps({'type': 'turn.completed', 'usage': {'input_tokens': 10}}),
        ]).encode()
        res = ledger_guard.audit_codex_events(good)
        self.assertEqual(res['violations'], [])
        self.assertEqual(res['malformed_lines'], [])
        self.assertTrue(res['has_turn_completed'])
        self.assertEqual(res['agent_message_count'], 1)

        bad = '\n'.join([
            json.dumps({'type': 'item.started', 'item': {'type': 'command_execution'}}),
            'NOT JSON',
        ]).encode()
        res2 = ledger_guard.audit_codex_events(bad)
        self.assertIn('command_execution', res2['violations'])
        self.assertTrue(len(res2['malformed_lines']) > 0)
        self.assertFalse(res2['has_turn_completed'])


class TestStaticAnalyzer(unittest.TestCase):
    def test_detects_nested_loops_recursion_and_float_risks(self):
        stmt = r'Constraints: $1 \le N \le 2 \times 10^5$, $1 \le K \le 10^{18}$.'
        src = (
            'def dfs(u):\n'
            '    return dfs(u - 1) if u > 0 else 0\n'
            'n = int(input())\n'
            'arr = []\n'
            'for i in range(n):\n'
            '    x = int(input())\n'
            '    for j in range(i):\n'
            '        y = sum(arr[j:i]) / 2\n'
        )
        facts = static_analyzer.analyze_python_source(src, stmt)
        self.assertTrue(facts['syntax_ok'])
        self.assertEqual(facts['max_loop_depth'], 2)
        self.assertIn('dfs', facts['recursive_functions'])
        self.assertFalse(facts['has_setrecursionlimit'])
        self.assertTrue(facts['uses_input_in_loop'])
        self.assertIn('sum(slice) inside loop', facts['has_quadratic_list_ops_in_loop'])
        self.assertTrue(facts['uses_float_ops'])
        self.assertEqual(facts['constraint_scales']['N'], 200000)
        self.assertEqual(facts['constraint_scales']['K'], 10**18)
        self.assertGreaterEqual(len(facts['risk_flags']), 4)
        summary = static_analyzer.format_static_summary(facts)
        self.assertIn('Recursion', summary)
        self.assertIn('Nested loops', summary)

    def test_handles_syntax_error_cleanly(self):
        facts = static_analyzer.analyze_python_source('def broken(:\n  pass\n', '')
        self.assertFalse(facts['syntax_ok'])
        self.assertTrue(facts['risk_flags'])


class TestManifests(unittest.TestCase):
    def test_frozen_manifests_exist_and_consistent(self):
        mp = json.loads(Path('enhanced_de/manifests/mutant_pool_final_main.json').read_text(encoding='utf-8'))
        self.assertEqual(mp['summary']['tasks_with_ref_and_public_pass_mutant'], 18)
        self.assertEqual(mp['summary']['distinct_public_pass_mutants'], 46)
        self.assertEqual(mp['summary']['distinct_all_mutants'], 123)

        val = json.loads(Path('enhanced_de/manifests/test5_val16.json').read_text(encoding='utf-8'))
        self.assertEqual(val['selected_counts'], {'medium': 8, 'hard': 8})
        self.assertEqual(len(val['tasks']), 16)
        self.assertEqual(val['shard_sha256'], tasks_v2.SHARD_SHA256['test5.jsonl'])


if __name__ == '__main__':
    unittest.main()
