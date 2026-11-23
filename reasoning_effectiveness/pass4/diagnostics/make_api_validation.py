"""Write the paid end-to-end API validation plan (C, D-active, E on arc192_a, seed 2108) for the selected agent.

usage: python reasoning_effectiveness/pass4/diagnostics/make_api_validation.py AGENT_ID
At most 1 paid request runs inside these attempts (E's diagnosis, only if E triggers); the plan and contract were
authored beforehand (2 requests). The pass-wide ledger caps everything at 20 requests / $10.
"""
import json
import sys
from pathlib import Path

G = 'E:/CSC2108Local/reasoning-effectiveness-pass4/guidance/p4-api-validation'
OUT = Path(__file__).resolve().parents[1] / 'plans/p4-api-validation.json'


def main(agent):
    t = 'lcb-atcoder-arc192_a'
    attempts = [
        {'task_id': t, 'condition': 'C', 'seed': 2108, 'agent': agent, 'variant': 'api', 'guidance': f'{G}/{t}.plan-v1.api.json'},
        {'task_id': t, 'condition': 'D', 'seed': 2108, 'agent': agent, 'variant': 'api-active',
         'guidance': f'{G}/{t}.contract-v3.api.json', 'injection': 'inject-active-v1', 'contract_checks': {'mode': 'active'}},
        {'task_id': t, 'condition': 'E', 'seed': 2108, 'agent': agent, 'variant': 'api',
         'diagnosis': {'provider': 'api', 'prompt_id': 'diagnosis-v1', 'delivery': 'deliver-v1', 'timeout': 300,
                       'purpose': 'pass4 end-to-end API validation of E under the final shared agent'}}]
    plan = {'batch': 'p4-api-validation', 'cohort': 'pass4 paid end-to-end API validation (consumed task)', 'frozen': False,
            'outer_timeout': 1000, 'attempts': attempts}
    OUT.write_text(json.dumps(plan, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(OUT)


if __name__ == '__main__':
    main(*sys.argv[1:])
