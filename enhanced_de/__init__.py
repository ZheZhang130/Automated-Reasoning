"""CSC2108 Enhanced Contract (D-v2) and Diagnosis (E-v2) exploratory research package.

Kept strictly separate from the frozen baselines (local_eval_v2, local_baseline,
local_optimization, guided_agent, judge, results/final-main). Reuses frozen
runtime bytecode via guided_agent.backend.bound_run without altering any of the
38 hash-verified frozen files.
"""

__all__ = [
    'ledger_guard',
    'static_analyzer',
    'tasks_v2',
    'mutant_pool',
]
