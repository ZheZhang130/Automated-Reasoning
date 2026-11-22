# Pass 3 readiness audit

Branch `feat/csc2108-contract-diagnosis-pass2`, which continues pass 2. Pass 3 started at `e254ccd` and the gate
was passed at `b9043ca`. Every statement below is marked by how it was established:

* **[tested]** an automated test or a real run;
* **[inspected]** reading code or records;
* **[assumed]** not verified.

## 1. What was working at the start

| Component | State at `e254ccd` | How known |
| --- | --- | --- |
| Frozen agent (`local_eval_v2.runtime.run`, 38 hashes, Qwen3.5 9B Q4_K_M `56671c2a…3c90`) | Verified on every attempt | [tested] `python -m local_agent verify` again in pass 3: 38 files, digest, images, Ollama 0.40.17 |
| A/B/C/D/E runner on the shared frozen loop | Working | [tested] 49 offline tests; 6 Docker E integration tests on the Windows and portable backends |
| Judge 0.2.1 (public and hidden containers) | Working for exact-output tasks | [tested] judge unit tests; [inspected] `judge/container/judge.py` |
| Codex isolated provider | Working | [tested] pass-2 live calls with 0 tool events |
| API ledger | Working, single process | [inspected] |

## 2. What was inconsistent, and what changed

| # | Problem found | Risk | Change (commit) | Verification |
| --- | --- | --- | --- | --- |
| 1 | **Output semantics were classified by one regex.** It missed case-insensitive judging (`arc192_b`, which was in the eligible pool) and constructive tasks that never say "any" (`arc195_c`: "If it exists, show one example."). | A correct program scored wrong | `guided_agent/output_semantics.py` (multi-cue classifier; any cue requires a manual review) and `evidence/output-semantics-review.json` (`9433efa`) | [tested] `JudgeSemantics` (9 tests); [inspected] the Output section of all 68 pilot/main tasks and all 25 pool tasks was read by hand |
| 2 | **The main 60 contain two non-exact tasks:** `arc195_c` (constructive, multiple valid outputs) and `abc395_a` (case-insensitive) | False negatives in the final benchmark | Documented (§3). The main manifest is not modified. | [inspected] |
| 3 | `judge/build_data.py` wrote CRLF on Windows, so manifest hashes failed. `guided_agent` worked around this with `_NoTranslatePath`. | A Windows judge build cannot be reproduced | `newline=""` on the three writes (`9433efa`). No change on POSIX. The workaround is kept, now redundant, because it produced the earlier data. | [tested] `test_build_data_writes_identical_lf_bytes_on_every_os` (CI on all three OSes) |
| 4 | **Run names had no seed.** Two attempts differing only in seed got the same directory, and the second was silently skipped as complete. | Silent loss of a condition run | `integrity.validate_plan` refuses duplicate names (`54e24cb`). Pass-3 seeds use separate batches. | [tested] `PlanIntegrity` |
| 5 | A frontier `coder` was accepted on any condition, and guidance on A/E | A mislabelled run | Plan validation plus runner guards. Only B substitutes a frontier coder; the scripted test coder is allowed outside frozen plans. | [tested] |
| 6 | Frozen benchmark plans could carry ACI options, smoke budgets or non-primary prompts | A silently changed configuration | `"frozen": true` plans are checked: no ACI or smoke; C=plan-v1, D=contract-v1, E=diagnosis-v1/deliver-v1; integer seeds | [tested] |
| 7 | `plan.json` was overwritten when a batch resumed | Configuration record not immutable | Resuming with a different plan is refused | [tested] `test_resumed_batch_must_keep_its_plan` |
| 8 | The GPU wait for foreign models ran for 2 h, then *started the attempt anyway*, so the frozen runtime failed it | A consumed attempt, recorded as an error | Bounded wait (`max_resource_wait`, default 1800 s), then the batch stops **before** the attempt with a `resource_unavailable` record. Your models are never unloaded. | [tested] `test_resource_wait_is_bounded_and_reports_unavailability` |
| 9 | API ledger read-modify-write had no lock; the ledger file's own `max_requests`/`max_usd` were trusted | Concurrent processes could lose a reservation; a ceiling could be raised | Exclusive lock file plus re-read; ceilings capped by the code constants | [tested] 20 concurrent reservations give exactly 12, then refusal |
| 10 | E did not check that the judged result came from the public suite, or that its hash equals the packet's candidate | Wrong evidence sent to the frontier | `qualifies` requires suite = public and `code_sha256` = snapshot | [tested]; [inspected] 290/290 past public calls already matched |
| 11 | `evaluate()` crashed on a malformed `result.json` | Lost hidden scores | Records `malformed_record` and continues | [inspected] |
| 12 | Codex provenance recorded the absolute binary path (with your Windows user name) and the temporary work directory | Privacy | Binary basename plus placeholder | [tested] `CodexProvenance` |
| 13 | CI did not run `guided_agent` | Regressions on macOS/Linux unseen | New `guided-agent` job on macOS, Ubuntu and Windows (`c81e2bc`, `b3f7163`, `26cc876`) | [tested] GitHub Actions [run 45060771955](https://github.com/ZheZhang130/Automated-Reasoning/actions/runs/45060771955): all six jobs green |

Two CI failures happened along the way and were fixed rather than skipped:

* `b3f7163`: `python -m unittest -v discover` is a usage error.
* `26cc876`: `scan(identity={})` fell back to the real identity, so the CI user name `runner` matched ordinary text.

## 3. Judge validation

**Rule [inspected].** Judge 0.2.1 implements LiveCodeBench's `grade_stdio`. It strips the output and each line,
requires equal line counts, and accepts a line if it is identical or if both sides parse to equal Decimal lists.
This rule is correct exactly when a task has one acceptable output text.

**Known failures reproduced [tested]** (`guided_agent/test_pass3.py`):

* **`abc392_d`, tolerance 1e-8.** `repr(1/3)` = `0.3333333333333333` is rejected against the reference
  `0.333333333333333`. The reference tolerance rule `checkers.tolerance_match` accepts it and rejects an error of 6.7e-8.
* **`abc396_e`, multiple minimum-sum outputs.** For `A1 xor A2 = 1`, `1 0` is rejected against `0 1`. The
  reference validator `checkers.xor_min_sum_valid` accepts it, and rejects a non-minimal sequence, a constraint
  violation and a wrong `-1`.

**Exact tasks unchanged [tested].** `checkers.compare('exact', …)` is the judge's own `outputs_match`,
extracted by AST from the deployed `judge/container/judge.py` (version string checked), on every host.

**Containment.**

* The checkers are reference implementations only. **No scoring was changed for any cohort.**
* Every pass-3 cohort task was reviewed as single-answer exact output before selection.
* Five pool tasks were excluded: four multiple-answer and one case-insensitive.
* Adopting tolerance, case or validator rules would mean a new judge version, introduced before a cohort is frozen.

**Inventory of non-exact tasks in the pinned shard (112 AtCoder tasks; manual review)**

| Task | Category | Where | Consequence |
| --- | --- | --- | --- |
| abc392_d | tolerance | pass-1 MB1 | Known historical false negatives (pass 1) |
| abc396_e | multiple answers | pass-1 MB2 | Known historical false negatives (pass 1) |
| arc192_a | case-insensitive | pass-1 development | All 10 historical submissions print canonical `Yes`/`No`: no false negative arose |
| **abc395_a** | case-insensitive | **main 60** | Risk only if a program prints non-canonical case |
| **arc195_c** | multiple answers (constructive) | **main 60** | Exact comparison rejects almost every correct program: exclude or add a validator before the final benchmark |
| abc397_d, abc398_f, arc190_a, arc191_c | multiple answers | pass-3 pool | Excluded |
| arc192_b | case-insensitive | pass-3 pool | Excluded (the pass-2 regex had missed it) |

**Other judge facts [inspected].**

* A few tasks have very few hidden files: `arc195_d` (pass-3 cohort), `abc399_d` and `arc196_b` (main) have
  one file each. These are multi-testcase files; arc195_d's is 675 KB against a 48-byte public file. They are valid
  but coarse: hidden scores are all-or-nothing on one file.
* **Hidden-test inaccessibility.**
  * judge-public loads only `tasks/<id>/tests/public` (`judgekit._suite_archive`).
  * The agent container mounts only `bundles/<id>`, read-only, at `/public` (integration log), with no network
    and all capabilities dropped.
  * Hidden scoring runs in a separate container after the batch.
  * The E packet holds only the statement, the judged candidate and the public report.
* **Independence from model feedback.** Hidden correctness is computed by `evaluate()` from `submission.py`
  bytes, after the batch, and the hash is checked. No model output is involved in scoring.
* **Line endings (Windows).** Fixed narrowly in `build_data.py` (item 3). Data previously built with the
  workaround is byte-identical.

## 4. Cross-platform CI

`.github/workflows/local-agent-portable.yml` now has two jobs on `macos-latest`, `ubuntu-latest` and `windows-latest`:

* **`host-contracts`** (unchanged): `local_agent` portability tests, offline verify and import of the original agent.
* **`guided-agent`** (new): `guided_agent.test_guided`, `test_pass2` and `test_pass3`.
  * **Scope:** E trigger, delivery, deadline accounting and provider failures; the B interface and the
    no-retry request cap; judge semantics; selection; plan integrity; the bounded resource wait; the
    concurrent ledger; Codex provenance; privacy; CLI smoke.
  * **Judge unit tests** run on POSIX. The judge container code imports `fcntl`.
  * **Backend:** Windows runners use the portable adapter (`CSC2108_TEST_BACKEND=portable`), because they
    have no `E:` data root.
  * **Constraints:** no model, no Docker sandbox, no network and no credentials.

**These are software tests, not inference validation.** No macOS run used the Qwen model; native Mac inference
remains unvalidated ([assumed] compatible; see `../PORTABILITY.md`).

Local results [tested]:

* Windows: 74 offline tests (65 `guided_agent` + 9 `local_agent`), 7 skipped integration tests, run three times
  with the windows backend and twice with the portable backend.
* The 6 Docker E integration tests pass on the pass-3 study.
* Judge unit tests pass in a Linux container (24, 18 Docker-gated skipped).

## 5. Provider isolation

* **Codex [tested]:** 24 pass-3 guidance artifacts.
  * Each event stream held exactly one `agent_message`, with 0 tool, command, file or search events.
  * No leftover files; `codex-cli 0.171.0`.
  * The isolated session gets only the versioned system prompt and the public statement (C/D), or the
    E evidence packet.
  * Credential-like variables are stripped from the child environment.
  * Codex does not report the serving model (`observed_model = null`); the requested model is `gpt-6.2-sol`, effort medium.
* **API [inspected and tested offline]:**
  * Raw HTTPS through `urllib`, with no client library and no retries.
  * One reserved, write-ahead ledger entry per request; ceilings 12 requests and $10 conservative.
  * The B coder's `_query` failures abort the agent (`abort_exceptions`) instead of being retried by tenacity,
    and its per-run cap raises `LimitsExceeded` before any request. Both are tested.
* **Pricing re-verified (2026-11-22)** on the
  [pricing page](https://developers.openai.com/api/docs/pricing) and the
  [model page](https://developers.openai.com/api/docs/models/gpt-6.2-sol): $2 / $10 per 1M input/output
  tokens standard. The ledger bound uses $12 / $60, above every listed tier for this request size.

## 6. Artifact privacy and provenance

**Scan of committed files [tested]:**

* No API keys, tokens or credentials.
* No email address or host name outside Git author metadata.
* The Windows user name appeared on 50 lines:
  * 49 committed Codex guidance artifacts from passes 1–2 (`isolation.command[0]`, the codex binary path),
    under `reasoning_effectiveness/evidence/guidance/` and `reasoning_effectiveness/pass2/evidence/guidance/`;
  * 1 README (`evidence/local_baseline/README.md`, a Docker disk path).

**Corrected by a normal commit:**

* The README path is redacted (`54e24cb`).
* New Codex records store only the binary basename (`54e24cb`).
* Every pass-3 export goes through `guided_agent.privacy.copy_sanitized_json`, which refuses a copy that still
  contains a home path, user or host name, or secret.
* `test_committed_pass3_files_have_no_home_paths_or_secrets` guards the pass-3 directory in CI.

**Not corrected (your decision).**

* **The 49 historical artifacts are unchanged.** Their SHA-256 values are recorded in the pass-1/2 freeze
  manifests and run records, so redacting them in place would break those recorded hashes. The brief forbids
  that without your permission.
* **Git history keeps the user name in any case.** Removing it there needs a history rewrite and a force-push,
  which were not done.
* **Options:**
  * (a) leave as is (documented exposure: user name only, no credentials);
  * (b) commit sanitized replacements, with a mapping from original to sanitized hashes;
  * (c) rewrite history.
* Full private provenance remains in `E:\CSC2108Local\…`.

## 7. Frozen baseline verification [tested]

`python -m local_agent verify` (pass 3, before any run) reported:

* frozen files: 38 verified;
* model: `qwen3.5:9b`, digest `56671c2a…3c90`, Q4_K_M, family `qwen35`;
* sampler: temperature 0.2, top-k 40, top-p 0.9, `num_predict` 4096, context 16384, thinking off;
* packages: mini-swe-agent 2.4.6, LiteLLM 1.81.16;
* images: `python:3.11-slim-bookworm` `a83ba18a…`, `csc2108-lcb-judge:v2` `00bc9f2a…`;
* system prompt sha `291f0f67…`;
* Ollama 0.40.17.

Every pass-3 attempt repeats this verification in its record.

The project Ollama server (port 11435) was started with `local_baseline/start_ollama.ps1`, after backing up its
logs to `E:\CSC2108Local\logs\*.pre-pass3-*.log`. Your Ollama (port 11434, its own process) had no model loaded
and was not touched.

## 8. Readiness gate (pass 3)

| Gate | Result |
| --- | --- |
| Common A/C/D/E runner passes its tests | **Pass** (offline 65 + 9; Docker E 6/6; CI green on three OSes) |
| Judge compatibility of the selected tasks | **Pass**: all 12 reviewed exact single-answer; non-exact tasks excluded before selection |
| Codex guidance and diagnosis providers work | **Pass**: 24/24 artifacts, 0 tool events; E Codex path as in pass 2 |
| Offline and synthetic E tests | **Pass** |
| Isolation and provenance | **Pass**, with the documented historical user-name exposure (§6) |
| Cohort frozen without outcome-based selection | **Pass**: `FREEZE-ext.json` (`dd57a95`) before guidance; `FREEZE-ext-guidance.json` (`b9043ca`) before any run |
| No unresolved infrastructure problem | **Pass** (one operational note below) |

**Operational note.** The first launch of the seed-2108 chain ran under a tool with a 2-hour cap. It was stopped
by me after about one minute and relaunched as a detached process. The interrupted first attempt
(`abc397_e-A`) is preserved as `abc397_e-A.incomplete-299a10` and was rerun by the batch's resume rule: same
seed, new run ID, before any result existed.

## 9. Remaining blockers before the final benchmark

1. **Judge.** `arc195_c` (constructive) and `abc395_a` (case-insensitive) in the main 60 need a decision:
   exclude them, or adopt a versioned judge with a validator and case folding, before the cohort is frozen.
2. **Task pool.** The test6 shard is exhausted apart from the main 60. There is no newer official shard
   (HF API: `code_generation_lite` last modified 2025-06-05, files `test.jsonl`–`test6.jsonl`). See
   `FINAL_BENCHMARK_OPTIONS.md`.
3. **Native macOS inference** is not validated.
4. **Historical privacy decision** (§6).
5. **The E provider for the final run** (API recommended): see `PROVIDER_VALIDATION.md`.
