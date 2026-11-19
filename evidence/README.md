# Research evidence and archives

Start with [RESULTS_SUMMARY.md](../RESULTS_SUMMARY.md) for current conclusions. This directory holds preserved research documents and aggregate artifacts, **not the runnable agent**. Use the [public interface](../local_agent/README.md) and [project map](../docs/PROJECT_STRUCTURE.md) for current behavior.

## Reports and archives

Historical documents retain their original wording, date-specific branch/push statements and relative links. Some links or commands refer to the old tree or machine artifacts and do not work from the relocated copy. Do not fix that history by editing the reports: use the original report at its commit below for original directory context, and current documentation for supported commands.

All five annotated archival tags were pushed before packaging. Commit-addressed links below identify their exact targets independently of whether old research branch names still exist.

| Stage | Preserved report/aggregate evidence | Archival tag and original report at its target commit |
| --- | --- | --- |
| Initial nine-run pilot | [Report](local_baseline/RESULTS.md), [model-location record](local_baseline/MODEL_LOCATIONS.md) | `archive/csc2108-local-pilot` ? [b978b7f150a52563da9a5f33568136fc792ee5bb](https://github.com/ZheZhang130/Automated-Reasoning/blob/b978b7f150a52563da9a5f33568136fc792ee5bb/local_baseline/RESULTS.md) |
| Extended three-model comparison | [Report](local_eval_v2/RESULTS.md), [CSV](local_eval_v2/benchmark_metrics.csv), [summary](local_eval_v2/benchmark_summary.json), [verification](local_eval_v2/benchmark_verification.json) | `archive/csc2108-extended-evaluation` ? [d0fb8756a54e7d7fb1f136b6a5de4a2257b3a4b9](https://github.com/ZheZhang130/Automated-Reasoning/blob/d0fb8756a54e7d7fb1f136b6a5de4a2257b3a4b9/local_eval_v2/RESULTS.md) |
| Optimization | [Report](local_optimization/REPORT.md), [held-out JSON](local_optimization/results/heldout-final.json), [CSV](local_optimization/results/heldout-final.csv), [charts](local_optimization/figures) | `archive/csc2108-qwen-optimization` ? [da6eb45a920004594f6fb14cc3baa87e143b5f16](https://github.com/ZheZhang130/Automated-Reasoning/blob/da6eb45a920004594f6fb14cc3baa87e143b5f16/local_optimization/REPORT.md) |
| One-shot pilot | [Report](one_shot_ablation/REPORT.md), [results](one_shot_ablation/results.json), [metrics](one_shot_ablation/metrics.csv), [verification](one_shot_ablation/verification.json) | `archive/csc2108-one-shot-ablation` ? [ca0e9dc1274e831d3f642a0b4e1730506c11f131](https://github.com/ZheZhang130/Automated-Reasoning/blob/ca0e9dc1274e831d3f642a0b4e1730506c11f131/one_shot_ablation/REPORT.md) |
| Delivery follow-up | [Report](agent_delivery_pilot/REPORT.md), [forensics](agent_delivery_pilot/FORENSICS.md), [results](agent_delivery_pilot/results.json), [verification](agent_delivery_pilot/verification.json), [75-ID exclusions](agent_delivery_pilot/future_exclusions.json) | `archive/csc2108-agent-delivery-followup` ? [f6ba40c6f284eb27c899fce60ffa1e73cdb36e26](https://github.com/ZheZhang130/Automated-Reasoning/blob/f6ba40c6f284eb27c899fce60ffa1e73cdb36e26/agent_delivery_pilot/REPORT.md) |

The three-model primary study is distinct from the smaller initial pilot and the superseded tag-default experiment. Read the current summary before comparing denominators or pooling results. The [exclusion list](agent_delivery_pilot/future_exclusions.json) contains the final 75 unique IDs under `exclude_from_future_fresh_validation`; earlier 65/71-ID lists are historical checkpoints.

[layout.json](layout.json) records paths and measured-file hashes for the prior packaging operation: 102 evidence files relocated and 24 old Python drivers retained only in archives. That map is historical and is not rewritten to describe this documentation review. [Prior handoff checks](handoff/README.md) and [verification](handoff/verification.json) record the completed packaging validation, including its synthetic model run; they do not claim that those executions were repeated during later documentation edits.

## Provenance and external artifacts

[Three-model provenance](local_eval_v2/benchmark_provenance.json) and [optimization provenance](local_optimization/results/provenance.json) preserve software versions, model digests/quantizations, prompts, source/test hashes, image identities and hardware. The frozen [selection](../local_optimization/final_selection.json) and [recommendation](../local_optimization/final_recommendation.json) remain runtime inputs at their original paths. Consult the [interface settings](../local_agent/README.md#frozen-configuration) for the selected default, rather than an exploratory profile in a historical report.

| Identity | Frozen record |
| --- | --- |
| Dataset | LiveCodeBench `code_generation_lite`, release v6, component `test6.jsonl` |
| Dataset revision | `0fe84c3912ea0c4d4a78037083943e8f0c4dd505` |
| Dataset SHA256 | `bb4c364f71921c4495a6ad15abe1a927350b720009f4933e2e71f8af0f6fd1f5` |
| Official evaluator revision | `28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24` |
| Agent image | `python:3.11-slim-bookworm`, ID `sha256:a83ba18aef0f865b1a4a611c2cf460fe446f2795673bbb9fe43be570439e3b39` |
| Judge image | `csc2108-lcb-judge:v2`, ID `sha256:00bc9f2a442ad4ec2cc98692313b3e6bab8752a765d724a8a79e47431b0c02ab` |

Full artifacts remain outside Git at these existing E: locations:

| Location | Contents |
| --- | --- |
| `E:\CSC2108Local\artifacts` | Original setup, sandbox, judge, model probe and pilot records |
| `E:\CSC2108Local\eval-v2` | Cached dataset, public/private bundles, synthetic fixtures and source archives |
| `E:\CSC2108Local\eval-v2\batches\extended-24-v6-common` | Primary 144-run three-model evidence |
| `E:\CSC2108Local\optimization` | Optimization trajectories, candidates, requests/responses, judges, logs and frozen source |
| `E:\CSC2108Local\one-shot-ablation` | Six-task paired pilot artifacts |
| `E:\CSC2108Local\agent-delivery-pilot` | Saved-trajectory forensics and four-task follow-up |
| `E:\OllamaModels` | Installed model weights/manifests |
| `E:\DockerDesktop` | Docker Desktop virtual disks/images/volumes |
| `E:\CSC2108Local\final-agent-handoff\20261118` | Prior packaging validation logs, sandbox controls and its single synthetic model run/judge |

Model weights, generated benchmark candidates, raw private cases, large trajectories and mutable runtime state are not committed. These machine locations are not created by cloning the repository, and no historical data is moved or deleted by documentation maintenance.
