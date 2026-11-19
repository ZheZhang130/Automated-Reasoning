# Research evidence and archives

Read [RESULTS_SUMMARY.md](../RESULTS_SUMMARY.md) first. This directory preserves the original reports and aggregate verification artifacts; it does not reinterpret their observations. Historical documents retain original relative links and time-specific branch/push statements. For their original directory context, use the immutable commits below.

| Stage | Evidence here | Archival tag and exact commit |
| --- | --- | --- |
| Initial pilot | [report](local_baseline/RESULTS.md) | [`archive/csc2108-local-pilot`](https://github.com/ZheZhang130/Automated-Reasoning/tree/archive/csc2108-local-pilot), `b978b7f150a52563da9a5f33568136fc792ee5bb` |
| Extended three-model evaluation | [report](local_eval_v2/RESULTS.md), `benchmark_*.json`, CSV | [`archive/csc2108-extended-evaluation`](https://github.com/ZheZhang130/Automated-Reasoning/tree/archive/csc2108-extended-evaluation), `d0fb8756a54e7d7fb1f136b6a5de4a2257b3a4b9` |
| Optimization | [report](local_optimization/REPORT.md), `results/`, charts | [`archive/csc2108-qwen-optimization`](https://github.com/ZheZhang130/Automated-Reasoning/tree/archive/csc2108-qwen-optimization), `da6eb45a920004594f6fb14cc3baa87e143b5f16` |
| One-shot pilot | [report](one_shot_ablation/REPORT.md), results/metrics/verification | [`archive/csc2108-one-shot-ablation`](https://github.com/ZheZhang130/Automated-Reasoning/tree/archive/csc2108-one-shot-ablation), `ca0e9dc1274e831d3f642a0b4e1730506c11f131` |
| Delivery follow-up | [report](agent_delivery_pilot/REPORT.md), forensics/results/verification/[75 exclusions](agent_delivery_pilot/future_exclusions.json) | [`archive/csc2108-agent-delivery-followup`](https://github.com/ZheZhang130/Automated-Reasoning/tree/archive/csc2108-agent-delivery-followup), `f6ba40c6f284eb27c899fce60ffa1e73cdb36e26` |

Annotated tags were created and pushed before cleanup. [layout.json](layout.json) records relocations/removals and hashes from the completed source working files. Required frozen files remain at original paths; [final_selection.json](../local_optimization/final_selection.json) retains their exact SHA256 map, frozen profile/image identities and preregistered rule. [final_recommendation.json](../local_optimization/final_recommendation.json) remains unchanged.

Provenance is available in [extended benchmark provenance](local_eval_v2/benchmark_provenance.json) and [optimization provenance](local_optimization/results/provenance.json): exact model digests, package/environment versions, prompts, datasets, source hashes, Docker IDs and hardware. Dataset: LiveCodeBench `code_generation_lite`, release v6 component `test6.jsonl`, revision `0fe84c3912ea0c4d4a78037083943e8f0c4dd505`, SHA256 `bb4c364f71921c4495a6ad15abe1a927350b720009f4933e2e71f8af0f6fd1f5`. Official evaluator: `28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24`.

Full historical artifacts remain **outside Git**, untouched at:

| Location | Contents |
| --- | --- |
| `E:\CSC2108Local\artifacts` | Original setup, sandbox, judge, model probe and pilot records |
| `E:\CSC2108Local\eval-v2` | Dataset cache, public/private bundles, synthetic fixtures, primary/superseded batches and source archives |
| `E:\CSC2108Local\eval-v2\batches\extended-24-v6-common` | Primary 144-run three-model evidence |
| `E:\CSC2108Local\optimization` | Full optimization trajectories, candidates, model requests/responses, judges, logs and frozen source |
| `E:\CSC2108Local\one-shot-ablation` | All six-task paired pilot artifacts |
| `E:\CSC2108Local\agent-delivery-pilot` | Saved-trajectory forensics and four-task three-way follow-up |
| `E:\OllamaModels` | Installed model weights/manifests |
| `E:\DockerDesktop` | Docker Desktop virtual disks/images/volumes |
| `E:\CSC2108Local\final-agent-handoff\20261118` | New packaging validation logs, sandbox controls and the single synthetic model run/judge |

Model weights, generated benchmark candidates, raw private tests, large trajectories and mutable runtime state are not included in this tree. No historical data directory was moved or deleted. Existing source/other branches remain intact. Completed handoff checks are summarized in [handoff/verification.json](handoff/verification.json).
