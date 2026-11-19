# Portability validation

This is software validation of the host adapter, not another model experiment. Existing Windows benchmark reports and all 38 frozen source files remain unchanged. No real Qwen inference, new benchmark task, frontier call or parameter search was run.

| Check | Observed result |
| --- | --- |
| Existing Windows interface and legacy suites, plus portable host contracts | 36 passed; one POSIX-only lock test skipped on Windows |
| Portable contracts inside Linux Python container | All 9 passed, including real POSIX lock contention/reuse and frozen Windows-style path normalization |
| Explicit portable provisioning on this Windows Docker host | Native AMD64 judge built successfully from the pinned multi-architecture Python base and original judge lock; native IDs/recipe recorded externally |
| ARM64 availability | Pinned Python registry index includes `linux/arm64/v8`; architecture guards tested with native ARM64 fixtures and reject mismatched/emulated images |
| Real mini-SWE-agent/LiteLLM/Docker against fake Ollama HTTP | Passed: 3 actions/calls, complete source write, public pass, submission, full trajectory; original rendered prompt, exact sampler/nonthinking mode and 20-action/3-repair/600-second limits verified |
| Separate official evaluator after that fake-server run | Synthetic candidate passed; judging made no extra model request |
| No-inference sandbox controls using newly built portable judge | Network/read-only/user/memory/CPU/PID/capability/mount isolation checked; public failure → changed repair → pass → submission; independent correct/wrong controls produced expected outcomes |
| Existing Windows `verify` | Original model digest, image IDs, Python/core versions and 38 hashes still pass; default backend remains Windows |
| Preservation | 240 old baseline and 30 forensic artifact hashes verified; historical reports/aggregates and teammate code unchanged |
| Static checks | Python compilation, current documentation links/anchors, Bash snippet syntax without execution and workflow YAML passed |

The [CI workflow](../.github/workflows/local-agent-portable.yml) installs the portable core pins, runs host contracts, performs offline integrity checks and imports the original agent on macOS, Windows and Linux. It deliberately has no model/Docker benchmark step. Actual run status is available in GitHub Actions; defining the workflow alone is not evidence that its remote jobs passed.

**A physical Mac/Metal inference run was not performed on this Windows development machine.** Unit/POSIX tests and the synthetic fake-server smoke validate host plumbing and agent/evaluator integration, not GPU performance or Mac benchmark accuracy. Follow [Mac acceptance checks](MACOS.md#3-check-isolation-then-run-a-task), then run a synthetic real-model task on the target Mac before research use. Intel CPU execution can exceed the fixed task budget; no budget or sampling change is made to compensate.

Full development records live outside Git under `E:\CSC2108Local\portability-validation`. Final native build/integration/control records are under `final-20261118`; Windows unit logs are under `prepared-20261118`. Earlier development failures and corrected smoke records remain preserved separately. Synthetic generated source/private rows and large trajectories are not committed.
