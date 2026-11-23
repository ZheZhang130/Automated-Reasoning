"""Write the stage-D plans for a selected shared-agent candidate (pass 4).

usage: python reasoning_effectiveness/pass4/diagnostics/make_stage_d.py AGENT_ID SHORT

Runs only what the historical frozen results (identical artifacts, verified deterministic) do not already cover:
* p4-stageD-agent:  A-candidate at seed 2109 (8), A-frozen at 2109 where no historical run exists (abc398_d, abc388_e),
                    C-candidate at 2108 and 2109 (16), C-frozen at 2109 where missing (abc393_d, abc398_d, abc388_e),
                    and one fresh C-frozen rerun at 2108 per two tasks as a determinism spot check (abc389_f, arc192_a);
* p4-stageD-de:     D-active and E (diagnosis-v1, live Codex) under the candidate at seed 2108 (8 + 8).
"""
import json
import sys
from pathlib import Path

TASKS = ['abc400_b', 'abc393_d', 'arc195_a', 'abc398_d', 'abc388_e', 'abc389_f', 'abc397_f', 'arc192_a']
PLANS = {'abc400_b': 'abc400_b.plan-v1.codex', 'abc393_d': 'abc393_d.plan-v1.api', 'arc195_a': 'arc195_a.plan-v1.codex',
         'abc398_d': 'abc398_d.plan-v1.codex', 'abc388_e': 'abc388_e.plan-v1.codex', 'abc389_f': 'abc389_f.plan-v1.codex',
         'abc397_f': 'abc397_f.plan-v1.codex', 'arc192_a': 'arc192_a.plan-v1.codex'}
G = 'E:/CSC2108Local/reasoning-effectiveness-pass4/guidance'
OUT = Path(__file__).resolve().parents[1] / 'plans'


def task(t):
    return 'lcb-atcoder-' + t


def main(agent, short):
    a = []
    for i, t in enumerate(TASKS):
        block = [{'task_id': task(t), 'condition': 'A', 'seed': 2109, 'agent': agent, 'variant': f'{short}-s2109'},
                 {'task_id': task(t), 'condition': 'C', 'seed': 2108, 'agent': agent, 'variant': f'{short}-s2108',
                  'guidance': f'{G}/p4-dev-plans/lcb-atcoder-{PLANS[t]}.json'},
                 {'task_id': task(t), 'condition': 'C', 'seed': 2109, 'agent': agent, 'variant': f'{short}-s2109',
                  'guidance': f'{G}/p4-dev-plans/lcb-atcoder-{PLANS[t]}.json'}]
        if t in ('abc398_d', 'abc388_e'):
            block.append({'task_id': task(t), 'condition': 'A', 'seed': 2109, 'agent': 'frozen-v6', 'variant': 'frozen-s2109'})
        if t in ('abc393_d', 'abc398_d', 'abc388_e'):
            block.append({'task_id': task(t), 'condition': 'C', 'seed': 2109, 'agent': 'frozen-v6', 'variant': 'frozen-s2109',
                          'guidance': f'{G}/p4-dev-plans/lcb-atcoder-{PLANS[t]}.json'})
        if t in ('abc389_f', 'arc192_a'):
            block.append({'task_id': task(t), 'condition': 'C', 'seed': 2108, 'agent': 'frozen-v6', 'variant': 'frozen-s2108',
                          'guidance': f'{G}/p4-dev-plans/lcb-atcoder-{PLANS[t]}.json'})
        a += block[i % len(block):] + block[:i % len(block)]
    plan = {'batch': 'p4-stageD-agent', 'cohort': f'pass4-dev8 stage D: {agent} vs frozen-v6 with A and C (consumed tasks)',
            'frozen': False, 'outer_timeout': 1000, 'attempts': a}
    (OUT / 'p4-stageD-agent.json').write_text(json.dumps(plan, indent=1) + '\n', encoding='utf-8', newline='\n')
    de = []
    for t in TASKS:
        de.append({'task_id': task(t), 'condition': 'D', 'seed': 2108, 'agent': agent, 'variant': f'{short}-active-s2108',
                   'guidance': f'{G}/p4-dev-v3/lcb-atcoder-{t}.contract-v3.codex.json', 'injection': 'inject-active-v1',
                   'contract_checks': {'mode': 'active'}})
        de.append({'task_id': task(t), 'condition': 'E', 'seed': 2108, 'agent': agent, 'variant': f'{short}-s2108',
                   'diagnosis': {'provider': 'codex', 'prompt_id': 'diagnosis-v1', 'delivery': 'deliver-v1', 'timeout': 300}})
    plan = {'batch': 'p4-stageD-de', 'cohort': f'pass4-dev8 stage D: D-active and E under {agent} (consumed tasks)',
            'frozen': False, 'outer_timeout': 1000, 'attempts': de}
    (OUT / 'p4-stageD-de.json').write_text(json.dumps(plan, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(len(a), len(de))


if __name__ == '__main__':
    main(*sys.argv[1:])
