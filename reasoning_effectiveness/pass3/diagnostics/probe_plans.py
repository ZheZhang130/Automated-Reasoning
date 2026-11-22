"""Plans for the pass-3 mechanism probe, provider checks and B real-task runs (development tasks only).

  python -m reasoning_effectiveness.pass3.diagnostics.probe_plans <study>

* probe-neutral: Condition E machinery at five FROZEN pre-trigger states from pass 2 (identical seed, statement
  and agent, so the trajectory up to the first public failure is byte-identical). The delivered text is a
  fixed, length-matched NON-diagnostic message with the same four headings and the same deliver-v1 wrapper.
  Compared with the genuine Codex diagnosis delivered at the same state in pass 2 and with A. Labelled a
  mechanism probe, never a condition, never pooled with the benchmark.
* api-checks: paid end-to-end validations (C via an API plan, D via an API contract, E via live API diagnoses
  at frozen states with recorded Codex counterparts).
* b-real: Condition B on two consumed development tasks (Codex coder; then one capped API coder run).
"""
import sys
from pathlib import Path

from guided_agent import guidance
from guided_agent.common import write_json
from guided_agent.integrity import validate_plan

NEUTRAL = """## Observed failure
The public test report above shows that the tested program did not produce the expected output on at least one public case. This message does not analyse that report or the program; it only restates that a public test failed.
## Likely cause
No cause has been identified here. A failure can come from many places in a program, for example from how the input is read, how the computation proceeds or how the answer is printed. This message deliberately makes no claim about which of these applies, and it does not point to any line of the program or to any part of the problem statement.
## Repair direction
Re-read the problem statement and the public test report above, decide for yourself what has to change, and revise /workspace/solution.py accordingly. Keep the program complete and runnable, reading standard input and printing to standard output.
## Verification target
After revising the program, run the public tests again with the usual command and check whether every public case now passes. Treat the task as finished only when the report shows that all public cases pass.
"""

# frozen trigger states (pass 2): task, seed, candidate sha256 prefix of the packet, genuine diagnosis words
STATES = [('lcb-atcoder-abc390_c', 2108, 'e6eafc9616', 187), ('lcb-atcoder-abc393_d', 2108, 'd099a73c6a', 200),
          ('lcb-atcoder-arc195_a', 2108, '597f9feaf6', 193), ('lcb-atcoder-arc195_a', 2109, '14660809c5', 183),
          ('lcb-atcoder-abc398_d', 2108, '0953cf427e', 199)]


def main(study):
    study = Path(study)
    assert not guidance.validate('diagnosis', NEUTRAL), guidance.validate('diagnosis', NEUTRAL)
    words = len(NEUTRAL.split())
    assert all(abs(words - w) <= 0.1 * w for *_, w in STATES), words
    probe = {'batch': 'probe-neutral', 'cohort': 'pass-3 mechanism probe (development tasks; not a condition)',
             'outer_timeout': 960,
             'attempts': [{'task_id': t, 'condition': 'E', 'seed': s, 'variant': f'neutral-s{s}',
                           'expected_candidate_prefix': prefix,
                           'diagnosis': {'provider': 'fixed', 'text': NEUTRAL, 'timeout': 300}}
                          for t, s, prefix, _ in STATES]}
    api_purpose = 'Pass-3 provider validation on a consumed development task'
    api = {'batch': 'api-checks', 'cohort': 'pass-3 direct-API end-to-end validation (development tasks)',
           'outer_timeout': 960, 'attempts': [
               {'task_id': 'lcb-atcoder-abc388_g', 'condition': 'C', 'seed': 2108, 'variant': 'api',
                'guidance': str(study / 'guidance/dev-api/lcb-atcoder-abc388_g.plan-v1.api.json')},
               {'task_id': 'lcb-atcoder-arc195_a', 'condition': 'D', 'seed': 2108, 'variant': 'api',
                'guidance': str(study / 'guidance/dev-api/lcb-atcoder-arc195_a.contract-v1.api.json')},
               {'task_id': 'lcb-atcoder-abc390_c', 'condition': 'E', 'seed': 2108, 'variant': 'api-s2108',
                'expected_candidate_prefix': 'e6eafc9616',
                'diagnosis': {'provider': 'api', 'timeout': 300, 'purpose': api_purpose + ': E at the frozen '
                              'abc390_c seed-2108 trigger (Codex counterpart in pass 2)'}},
               {'task_id': 'lcb-atcoder-arc195_a', 'condition': 'E', 'seed': 2109, 'variant': 'api-s2109',
                'expected_candidate_prefix': '14660809c5',
                'diagnosis': {'provider': 'api', 'timeout': 300, 'purpose': api_purpose + ': E at the frozen '
                              'arc195_a seed-2109 trigger (Codex counterpart in pass 2)'}}]}
    b_codex = {'batch': 'b-real-codex', 'cohort': 'pass-3 Condition B on real development tasks (Codex-replay coder)',
               'outer_timeout': 2400, 'attempts': [
                   {'task_id': t, 'condition': 'B', 'seed': 2108, 'variant': 'codex',
                    'coder': {'provider': 'codex', 'max_requests': 28, 'effort': 'medium'}}
                   for t in ('lcb-atcoder-abc391_a', 'lcb-atcoder-abc393_d')]}
    b_api = {'batch': 'b-real-api', 'cohort': 'pass-3 Condition B on a real development task (direct API coder)',
             'outer_timeout': 1800, 'attempts': [
                 {'task_id': 'lcb-atcoder-abc393_d', 'condition': 'B', 'seed': 2108, 'variant': 'api',
                  'coder': {'provider': 'api', 'max_requests': 6, 'effort': 'medium', 'max_completion_tokens': 8000,
                            'purpose': 'Pass-3 Condition B real-task cost/reliability (abc393_d, cap 6 requests)'}}]}
    for plan in (probe, api, b_codex, b_api):
        problems = [p for p in validate_plan(plan) if 'does not exist' not in p]
        if problems:
            raise SystemExit(problems)
        write_json(study / 'plans' / f"{plan['batch']}.json", plan)
    print('neutral words', words, '; plans written')


if __name__ == '__main__':
    main(sys.argv[1])
