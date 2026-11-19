# Completed local-agent results

**Retain Qwen3.5 9B with the original `heredoc-v6-16k-common` configuration.** The optimization challenger failed its preregistered promotion rule, and the delivery-prompt intervention showed no improvement. These studies do not establish that mini-SWE-agent inherently helps or hurts coding accuracy compared with one-shot generation. For usage and exact settings, see the [public interface](local_agent/README.md); for folder roles, see [project structure](docs/PROJECT_STRUCTURE.md).

| Study | Official correctness | Interpretation |
| --- | --- | --- |
| Primary common-sampler three-model comparison | Qwen3.5 9B **23/48**; Qwen2.5-Coder 14B **18/48**; 7B **15/48** | 24 problems × 2 seeds per model, 144 attempts total; selected 9B as the practical local model |
| Optimization held-out comparison | Original **19/40**; challenger **22/40** | 20 problems × 2 seeds; challenger used **12.5% fewer observed output tokens**, but was **not promoted** |
| Shortened-budget one-shot ablation | Agent **3/6**; one-shot **4/6** | 120 seconds/task, agent at most 10 actions/3 repair groups; one correctness disagreement favored one-shot |
| Delivery-prompt follow-up | Original agent **1/4**; modified-prompt agent **1/4**; one-shot **1/4** | Same shortened budgets; no improvement; **do not promote** the prompt-only intervention |

The primary three-model comparison above is separate from the initial nine-run pilot and the superseded unequal-tag-sampler experiment; their observations are not pooled into those scores. Historical reports for all stages are indexed in [evidence](evidence/README.md#reports-and-archives).

The optimization challenger failed the preregistered confirmation requirements: the paired problem-bootstrap 95% interval was [0, +15 percentage points], and missing submissions increased from 8 to 9. Its token totals were 241,025 versus 275,593 observed output tokens (12.5% fewer after rounding). A better point estimate alone was insufficient.

The six-task and four-task pilots are small exploratory samples. Agent execution permits multiple model calls, public feedback and repairs; one-shot permits a single call. They do not match inference opportunities or compute and are **not causal estimates** of agent effectiveness under matched compute. The follow-up's four IDs were fresh, but their contests were previously represented. The prior handoff's synthetic validation task adds no benchmark observation; documentation maintenance runs no inference.

Observed failures include long planning comments embedded inside Python source exhausting the 4,096-token response cap before the command fence closes, substantial inference time spent delivering invalid/incomplete actions, repeated unchanged edits and ineffective debugging. A reported candidate file can also be an unchanged starter. Public-test accounting recognizes a narrow set of direct checker commands; compound commands can execute tests without incrementing its recognized-test counters. This known baseline limitation is preserved and disclosed.

Earlier thinking, larger-context/output and native-tool studies did not establish a better practical default. The unsuccessful prompt-only intervention does not answer whether substantive frontier planning would help; that remains a future experiment.

Original evidence, preserved without changing observations:

- [Three-model report](evidence/local_eval_v2/RESULTS.md), [metrics](evidence/local_eval_v2/benchmark_metrics.csv), [summary](evidence/local_eval_v2/benchmark_summary.json), [verification](evidence/local_eval_v2/benchmark_verification.json), [full provenance and prompts](evidence/local_eval_v2/benchmark_provenance.json).
- [Optimization report](evidence/local_optimization/REPORT.md), [held-out aggregates](evidence/local_optimization/results/heldout-final.json), [CSV](evidence/local_optimization/results/heldout-final.csv), [frozen recommendation](local_optimization/final_recommendation.json), [verification](evidence/local_optimization/results/final_integrity.json).
- [One-shot report](evidence/one_shot_ablation/REPORT.md), [results](evidence/one_shot_ablation/results.json), [verification](evidence/one_shot_ablation/verification.json).
- [Delivery report](evidence/agent_delivery_pilot/REPORT.md), [forensics](evidence/agent_delivery_pilot/FORENSICS.md), [results](evidence/agent_delivery_pilot/results.json), [verification](evidence/agent_delivery_pilot/verification.json).
- [Final 75-ID exclusion list](evidence/agent_delivery_pilot/future_exclusions.json): use the `exclude_from_future_fresh_validation` field for future fresh-task selection; earlier exclusion counts are historical checkpoints.

See the [evidence index](evidence/README.md) for immutable archival commits, dataset/evaluator identities and external artifact locations.
