"""Offline tests for trigger partitioning (run_phase2_validation) and the Phase 3 selector.  No GPU, Docker or API."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from guided_agent.common import write_json

from . import run_phase2_validation as p2
from . import run_phase3_api as p3


def _run(tmp, name, *, arm='A', seed=2108, task='lcb-atcoder-x', reasons=(), statuses=(), sha='s', triggered=False,
         delivered=False, hidden='pass', batch=None):
    batch = batch or p2.batch_dir(tmp)
    d = Path(batch) / name
    d.mkdir(parents=True)
    rec = {'run_id': name, 'task_id': task, 'seed': seed, 'arm': arm, 'condition': arm[:2],
           'exit_status': 'submitted', 'submission_sha256': sha,
           'guidance': {'triggered': triggered, 'delivered': delivered},
           'usage': {'coding': [{'done_reason': r, 'completion_tokens': 10} for r in reasons]}}
    write_json(d / 'result.json', rec)
    (d / 'attempts.jsonl').write_text(''.join(
        json.dumps({'action': i + 1, 'result': {'status': s}, 'delivered': True}) + '\n' for i, s in enumerate(statuses)),
        encoding='utf-8')
    write_json(Path(batch) / 'eval' / f'{name}.json', {'status': hidden, 'passed': 40 if hidden == 'pass' else 3,
                                                        'total': 40})
    return d, rec


class TriggerStates(unittest.TestCase):
    def test_stall_fail_pass_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            d, rec = _run(tmp, 'r1', reasons=('length', 'length', 'stop'), statuses=('candidate_failure', 'pass'))
            st = p2.trigger_states(d, rec)
            self.assertTrue(st['stall'] and st['fail'] and st['pass'])

    def test_single_length_stop_is_not_a_stall(self):
        with tempfile.TemporaryDirectory() as tmp:
            d, rec = _run(tmp, 'r1', reasons=('length', 'stop', 'length'), statuses=('pass',))
            st = p2.trigger_states(d, rec)
            self.assertFalse(st['stall'])
            self.assertFalse(st['fail'])
            self.assertTrue(st['pass'])


class Compose(unittest.TestCase):
    def test_dormant_cells_come_from_a_and_composites(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks = ['lcb-atcoder-t1', 'lcb-atcoder-t2', 'lcb-atcoder-t3']
            # t1: stall then fail (A fails); t2: public pass (A passes); t3: public failure only (A fails)
            _run(tmp, 'a1', task=tasks[0], reasons=('length', 'length', 'stop'), statuses=('candidate_failure',),
                 hidden='candidate_failure', sha='a1')
            _run(tmp, 'a2', task=tasks[1], reasons=('stop',), statuses=('pass',), sha='a2')
            _run(tmp, 'a3', task=tasks[2], reasons=('stop',), statuses=('candidate_failure',),
                 hidden='candidate_failure', sha='a3')
            _run(tmp, 's1', arm='E2-stall-diag', task=tasks[0], triggered=True, delivered=True, sha='x')
            _run(tmp, 'f1', arm='E2-strict', task=tasks[0], triggered=True, delivered=True, sha='y',
                 hidden='candidate_failure')
            _run(tmp, 'f3', arm='E2-strict', task=tasks[2], triggered=True, delivered=True, sha='z')
            _run(tmp, 'r2', arm='E2-review', task=tasks[1], triggered=True, delivered=False, sha='a2')
            states = {}
            for name, t in (('a1', tasks[0]), ('a2', tasks[1]), ('a3', tasks[2])):
                d = p2.batch_dir(tmp) / name
                states[t] = p2.trigger_states(d, json.loads((d / 'result.json').read_text()))
            write_json(Path(tmp) / 'reports' / 'phase2_trigger_states_s2108.json',
                       {'states': states, 'counts': {}})
            with mock.patch.object(p2, 'task_ids', return_value=tasks):
                out = p2.compose(tmp, 2108)
            cells, table = out['cells'], out['table']
            self.assertEqual(table['A']['passes'], 1)
            # strict: live on t1 (fail) and t3 (pass); t2 has no public failure -> from A (pass)
            self.assertEqual(cells['E2-strict'][tasks[1]]['source'], 'from_A (trigger state not reached)')
            self.assertEqual(table['E2-strict']['passes'], 2)
            # stall-full: t1 from stall-diag (pass), t2 from A (no stall, no fail -> A), t3 from strict (pass)
            full = cells['E2-stall-full (composed)']
            self.assertTrue(full[tasks[0]]['source'].startswith('composed from E2-stall-diag'))
            self.assertTrue(full[tasks[2]]['source'].startswith('composed from E2-strict'))
            self.assertEqual(table['E2-stall-full (composed)']['passes'], 3)
            # adaptive composite uses review on the public-pass-only task
            self.assertTrue(cells['E2-adaptive (composed: stall > fail > review)'][tasks[1]]['source']
                            .startswith('composed from E2-review'))
            # a silent review that reproduces A is not flagged as non-deterministic
            self.assertEqual(table['E2-review']['untriggered_live_not_same_as_A'], [])


class Phase3Selector(unittest.TestCase):
    def test_reads_trigger_file_and_labels_fallbacks(self):
        with tempfile.TemporaryDirectory() as tmp:
            states = {
                'lcb-atcoder-abc384_c': {'stall': False, 'fail': True, 'pass': True},
                'lcb-atcoder-abc383_c': {'stall': True, 'fail': False, 'pass': False},
                'lcb-atcoder-abc379_g': {'stall': False, 'fail': False, 'pass': False},
            }
            write_json(Path(tmp) / 'reports' / 'phase2_trigger_states_s2108.json', {'states': states})
            t = p3.select_phase3_targets(tmp)
            self.assertEqual(t['d2_oracle_api'], [('lcb-atcoder-abc384_c', 2108, 'test5')])
            self.assertEqual(t['e2_strict_api'][0], ('lcb-atcoder-abc384_c', 2108, 'test5'))
            self.assertEqual(len(t['e2_strict_api']), 4)
            self.assertTrue(all(src.startswith('dev-') for _, _, src in t['e2_strict_api'][1:]))
            self.assertEqual(t['e2_stall_api'][0], ('lcb-atcoder-abc383_c', 2108, 'test5'))
            self.assertEqual(t['e2_review_api'][0], ('lcb-atcoder-abc384_c', 2108, 'test5'))


if __name__ == '__main__':
    unittest.main()
