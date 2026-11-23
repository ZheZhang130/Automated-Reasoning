# guided_agent: the integrated A/B/C/D/E runner

Every condition runs on **one** coding agent: the unchanged frozen `local_eval_v2/runtime.run` (mini-SWE-agent
2.4.6, Qwen3.5 9B, `heredoc-v6-16k-common`) with the shared-agent configuration from `agent_config.py`. Public tests
go through the team judge-public; hidden scoring is a separate step. Start with `../HANDOFF_TO_PETER.md`.

| Module | Role |
| --- | --- |
| `__main__.py` | CLI: `prepare-tasks`, `prepare-fixture`, `author`, `batch`, `run-one`, `evaluate`, `summarize`, `measure`, `schema` |
| `runner.py` | one attempt → `result.json`, `attempts.jsonl`, `submission.py`, `measurement.json`; hard outer timeout; hidden `evaluate` |
| `backend.py` | rebinds `Agent` (first-message template, E delivery) and `Environment` (judge-public routing, E trigger) in the frozen function; composes with the portable host adapter |
| `agent_config.py` | versioned shared-agent configurations (`frozen-v6`, `l1-selfplan-v1`; `PRIMARY_AGENT`) |
| `guidance.py` | versioned prompts (`plan-v1`, `contract-v1`, `diagnosis-v1`), injection and delivery templates, validation, write-once statement-bound artifacts |
| `diagnosis.py` | E: trigger policy, evidence packet, Codex / API / fixed / replay providers, at-most-once controller with deadline suspension |
| `frontier_coder.py` | B: API (ledgered, per-run cap), Codex-per-turn and scripted coders as a model substitution |
| `providers.py` | isolated Codex inference; direct OpenAI client with the write-ahead request/cost ledger |
| `measurement.py` | the stable measurement record (`csc2108-run-measurement-v1`) |
| `integrity.py` | plan validation; frozen plans accept only the primary configuration |
| `tasks.py`, `selection*.py`, `output_semantics.py`, `checkers.py` | judge tasks and bundles from the pinned shard; outcome-blind selection; judge-compatibility classification (`data/output-semantics-review.json`) |
| `analysis.py`, `privacy.py` | quick per-batch summary; sanitization for committed evidence |
| `fixtures/` | sanitized run records for pipeline tests (no model needed) |
| `test_*.py` | offline tests; Docker integration tests with `CSC2108_INTEGRATION=1` |
