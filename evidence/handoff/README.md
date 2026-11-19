# Final component validation — 2026-11-18

All checks passed using the existing environment. [verification.json](verification.json) is the aggregate record. Full logs, synthetic candidates and complete model trajectories remain at `E:\CSC2108Local\final-agent-handoff\20261118`; no benchmark inference was performed.

| Check | Outcome |
| --- | --- |
| Compilation and runtime/selected/judge/wrapper imports | Passed |
| `local_agent.test_interface` | 4 passed: frozen identity, changed-source rejection, missing/partial telemetry, artifact destination |
| `local_baseline/test_runner.py` | 6 passed: action/repair limits, containment, public/private export separation |
| `local_eval_v2` tests | 9 passed: scheduling/resume/interruption, submission hooks, actual LiteLLM sampler serializer, paired accounting |
| `local_optimization` tests | 9 passed: real provider serializer, typed timeout, original control, split/exclusion/private separation, checker matching |
| No-inference Docker integration controls | Public-only read-only bind; no network; unprivileged/capped resources; malformed action rejected; real persistent writes; public failure → changed repair → pass; final submission |
| Independent evaluator controls | Existing Qwen-authored toy passed; wrong and syntax controls failed; deliberate memory-only OOM identified through owned-container evidence |
| Single original-profile synthetic model task | `dev-negative-squares`: Submitted, 3 actions/calls, 175 output tokens, 0 format errors, public test passed, complete trajectory |
| Separate official synthetic evaluation | Passed; candidate SHA256 `2e91f486dc6b954cca33a897f786fd37ee1c78ad160f505cbf5f2e4ccf435611` |
| Actual requests | Original rendered system prompt, nonthinking flag and exact frozen sampler verified across all 3 calls |
| Source/data preservation | 38 frozen files and 102 relocated evidence files byte-identical; 240 older baseline artifact hashes and 30 forensic artifact hashes verified; 75 unique exclusions retained |
| Fresh checkout byte integrity | Staged-index export passed offline profile/prompt/package/hash verification; Git attributes preserve the measured line endings |
| Source branch and teammate files | Original worktree clean at `f6ba40c`; orchestration/timeline bytes unchanged; five archival tags verified remotely |

The synthetic wrapper invocation took 31.860 seconds (29.219 seconds in the original runtime, including 20.282 seconds of model load). Independent judging took 2.750 seconds. Only one model attempt was run. After it finished, two observational fields were added to the wrapper output: run identity and verified image IDs. No launch/model logic changed; final code passed all 28 tests and static checks. Both execution-time and final wrapper hashes are retained in verification.

No baseline behavioral change was required. Checkout attributes repair byte preservation, and the new interface adds identity checks and output packaging. Historical drivers that are not part of the supported interface remain archived or pinned as described in the dependency note. This deployment still requires the existing Windows/E: environment and trusted prepared Python bundles; arbitrary repository repair and frontier planning remain future integration work.
