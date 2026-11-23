# Run-record fixtures for pipeline tests

Sanitized records of real attempts (passes 3–4) and scripted integration runs. They let the evaluation pipeline
be tested without running any model.

**Contents of each `<role>/` directory:**

* `result.json`: the run record, with long texts replaced by `sha256:<hash>`;
* `measurement.json`: schema `csc2108-run-measurement-v1`; see `MEASUREMENT_SCHEMA.md`;
* `attempts.jsonl`: judge-public history, with report texts hashed;
* `eval.json`: the hidden verdict, where the run was scored. Scripted integration runs have no hidden verdict.

**Never included:** user names, host names, home paths, secrets, candidate programs, statements, model texts and
hidden tests. `privacy.scan` checks every file.

`INDEX.json` lists the roles:

| Role | What it exercises |
| --- | --- |
| `a_success` | local-only success, hidden pass |
| `a_selfplan_success` | the documented alternative shared agent `l1-selfplan-v1` (not primary): self-plan call recorded under `local_inference.self_plan`, hidden pass |
| `a_truncated_no_program` | three output-cap truncations, `RepeatedFormatError`, no submission (`missing_submission`) |
| `a_action_budget` | 20-action limit reached with a program on disk (scripted) |
| `c_success` | upfront plan (Codex replay), `frontier.requests[0].upfront = true`, hidden pass |
| `d_passive_contract` | upfront contract, wrong program (hidden failure) |
| `e_triggered_repair` | E trigger, live diagnosis, repair in the same session, hidden pass |
| `e_untriggered` | E assigned but never triggered (no program reached a public test) |
| `e_provider_error` | E triggered, provider failure recorded, agent continued (scripted) |
| `b_frontier_api_repair` | B via the direct API: 7 ledgered requests with measured cost, self-repair, hidden failure |
| `c_context_overflow` | the prompt reached the 16K context: Ollama connection error, runner exit `infra_error`, but `correctness.context_overflow = true` and `infrastructure_failure = false` (deterministic; count as a failure) |
| `infrastructure_error` | judge infrastructure error, `correctness.infrastructure_failure = true` (scripted) |

Regenerate with `python reasoning_effectiveness/pass4/diagnostics/export_fixtures.py` on the development branch.
