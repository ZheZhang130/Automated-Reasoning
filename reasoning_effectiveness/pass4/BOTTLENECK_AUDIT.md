# Bottleneck audit: which limits of the shared agent are artificial? (pass 4, Phase I)

**Scope.**

* **Agent audited:** the original frozen agent `frozen-v6` (mini-SWE-agent 2.4.6, `local_eval_v2/runtime.run`,
  Qwen3.5 9B Q4_K_M `56671c2a…3c90`, profile `heredoc-v6-16k-common`), as used by A/C/D/E in passes 1–3.
* **Code paths:** read directly. Ollama 0.40.17 and LiteLLM 1.81.16 behaviour was **checked on the wire** in this pass.
* **Run evidence:** all 217 original-agent runs of passes 1–3 (A 52, C 49, D 74, E 42), via
  `diagnostics/bottleneck_evidence.py` and `diagnostics/format_errors.py`. Outputs:
  `evidence/bottleneck-evidence-summary.json` and `evidence/format-errors-summary.json`.
* **Prior studies on this model:** the teammates' earlier sampler and protocol study (`evidence/local_optimization/REPORT.md`)
  and one-shot pilot (`evidence/one_shot_ablation/REPORT.md`). These are cited where they already answer a question;
  they are not repeated.

**Bottom line.**

* **The binding constraint is the 4,096-token output cap combined with a protocol that puts all reasoning inside
  the file being written.** All 82 runs (of 217) that ended without a program ended on three consecutive cap hits.
* **Time, context, observation size, request timeouts, the action limit and the repair limit almost never bind.**
* The audit therefore motivates the four screened changes:
  * **L1:** separate local reasoning;
  * **L2:** thinking;
  * **L3:** a larger output allowance;
  * **L4:** state receipts after edits.

  Their results are in `LOCAL_AGENT_EXPERIMENTS.md`.

## 1. Where the 217 runs end

| Exit | Runs | Comment |
| --- | --- | --- |
| Submitted | 111 | 88 hidden passes over all conditions |
| **RepeatedFormatError** | **82** | **every** run without a program; all 82 terminal triples are output-cap hits |
| RepairLimit (more than 3 repair groups) | 12 | wrong algorithm, kept editing |
| ActionLimit (20 actions) | 11 | 7 contain identical-rewrite loops (≥2 exact repeats; pass 3 §2). None recorded a public pass, though one (abc395_f, A, seed 2108) held a hidden-correct program it never retested or submitted |
| CommandExecutionError | 1 | one C run; a command timed out |
| Deadline (600 s) or model-request timeout (180 s) | **0** | the slowest run took 307 s |

Format errors: **322 of 324** are `finish_reason = length` at exactly 4,096 tokens; 2 are other parse failures. 52 runs
recovered from at least one format error (the retry is not useless), and 82 did not.

## 2. Limits and design choices, one by one

Columns:

* **Research or engineering?** Is the choice part of the experimental design, or an engineering choice?
* **Binding?** Is it observed to constrain outcomes in the 217 runs?
* **Fair to relax?** Does relaxing it change experimental fairness? Every change applies to all local conditions.

| Item | Implemented at | Why it exists | Research or engineering? | Binding? | Fair to relax? | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| Model Qwen3.5 9B Q4_K_M | `local_agent`, `MODELS` | the project's local model | research | — | no | retain |
| Context 16,384 (`num_ctx`) | `profiles.json` | fits the 16 GB GPU with headroom; teammates' selection | engineering | **no**: max prompt 13,825 tokens, 5 runs above 12K, 0 context-cap stops; the teammates found 16K→32K removed context stops without a correctness change | yes | retain (32K is used where the output allowance grows) |
| Output cap 4,096 (`num_predict`) | `profiles.json` | bounds a single response | engineering | **yes**: 322 cap stops; 126 of 217 first responses truncated; all 82 no-program runs | yes, if applied to all | **tested (L3)** |
| Thinking off (`think: false`) | `profiles.json` → `kwargs['think']` | teammates found thinking slower and no better | engineering | indirectly: reasoning has no channel except the file | yes | **tested (L2)** |
| T=0.2, top_p 0.9, top_k 40, min_p 0, penalties 0, repeat window 64, fixed seed | `profiles.json` `sampler` | reproducibility; selected by the teammates' study | engineering | partly: low temperature makes identical-rewrite loops a deterministic fixed point (pass 3 §5.2) | yes | retain. Already studied: presence 1.5 + window 1024 gave +3/40 but the interval touched 0, not promoted. A vendor preset reversed on fresh tasks. |
| One fenced command per response; "Return just the ONE current command block" | `runtime.PROMPT`, `action_regex` | mini-SWE-agent text protocol | research (the shared ACI) | **yes, indirectly**: median prose before the fence is 0 characters; deliberation happens as comments inside the heredoc | a change to the protocol would apply to all | **tested (L1)**: a bounded reasoning step outside the action protocol |
| Format-error retry, 3 consecutive (`max_consecutive_format_errors`) | mini-SWE-agent default | stop a model that cannot act | engineering | yes: terminal in 82 runs; recovers in 52 | yes | retain; it is the symptom, not the cause |
| Format-error message (length branch) | `runtime.FORMAT_ERROR` | feedback after a rejected response | engineering | weak: P(truncated after truncated) is 77% in pass 3 | — | retain. aci-v2's longer message lowered persistence a little but did not stop in-file deliberation |
| 20 actions (`Budget`), `step_limit` = 28 model calls | `local_baseline/runner.Budget`, `runtime.run` | equal opportunity, bounded cost | research | rarely: 11 runs, none after a public pass | — | retain |
| 3 repair groups | `Budget.changed` | bounded repair | research | rarely: 12 runs, all with wrong algorithms | — | retain |
| 600 s coding time; 180 s per request | `runtime.run`, `Agent.query` | bounded wall time | research | **never** (max 307 s) | — | retain |
| Sandbox command timeout 27 s, `ulimit -f 2048`, output head 16,384 bytes | `TaskEnvironment.execute` | safety | engineering | once (1 command timeout) | — | retain |
| Observation clip 6,000 characters | `observation_template` | context protection | engineering | **never** (0 of 1,182 observations) | — | retain |
| Empty observation after a successful write (`<returncode>0</returncode>`) | `observation_template` with an empty output | upstream default | engineering | **yes**: precedes 69 of 77 identical rewrites (pass 3 §2) | yes | **tested (L4)** |
| Public test = judge-public report | `backend.JudgedEnvironment._public_judge` | team judge, real expected outputs | research | — | — | retain |
| Candidate extraction = last snapshot | `TaskEnvironment.last_candidate` | the submission is the saved file | engineering | — | — | retain. A truncated heredoc is never salvaged: 0 of 38 parsable truncated prefixes passed any public case (pass 3 §5.1) |
| Container lifetime 660 s (E: +330 s); outer supervisor 960 s (E: +330 s) | `runtime.run`, `cmd_batch` | cleanup | engineering | never | — | retain |
| No budget information shown to the model | `PROMPT`, observations | upstream default | engineering | unknown: E's delivery message is the only place the model learns "N actions left" | yes | part of L4's receipt |

## 3. Thinking mode and the adapters, verified on the wire

Probe: `scratchpad think_probe` (not committed); the agent-level traces are in the L2 runs.

* **Separation works.** Ollama 0.40.17 returns `message.thinking` separately from `message.content`. LiteLLM 1.81.16
  (`ollama_chat`) maps it to `reasoning_content` and leaves `content` clean. The text protocol parses only
  `content`.
* **One shared cap.** `num_predict` limits thinking and answer **together**. With a 128-token cap the response ended
  with `done_reason = length`, 403 characters of thinking and **empty content**. Under the agent that is a format
  error with no action: at 4,096 tokens the agent cannot act whenever thinking needs the whole allowance.
* **History.** mini-SWE-agent stores `reasoning_content` in the assistant message, and LiteLLM resends it as
  `thinking`. Qwen3.5's Ollama template drops earlier turns' thinking: prompt tokens grow only by the visible
  content (L2 abc400_b: 595 → 830 → 876 prompt tokens after 3,013 and 110 thinking characters). So thinking
  does not inflate the context.
* **Telemetry.** `eval_count` includes thinking tokens. Ollama does not report thinking tokens separately, so the
  records give thinking **characters** and total generated tokens; a separate thinking-token count is recorded as
  unavailable, not zero.
* **Earlier result.** The teammates' study found thinking at 4K failed to act on medium and hard tasks, and 32K
  thinking was too slow (one success at 26K tokens and 306 s). L2 therefore tests 8K thinking with a 32K context.

## 4. The action protocol (brief §5.2)

* **Can the agent reason before writing code?** The prompt allows nothing but "the ONE current command block".
  The model complies: the median prose before the fence is 0 characters (pass 3), so on unfamiliar problems the
  method is searched for *inside* the heredoc, as comments, until the cap. Nothing in the protocol gives reasoning a
  place that survives truncation. **That is the strongest candidate for an artificial limitation.** C works around
  it because the plan arrives before the first action: its first files are mostly code (pass 3 §1).
* **Is the fenced-command parser appropriate?** For the responses that close the fence, yes: 2 of 324 format errors
  are parse failures. Native tool calling was studied by the teammates. The installed LiteLLM serializer drops
  assistant tool calls from the history, and a corrected transport reached 2/3 versus the control's 2/3 at about
  twice the time. It was not promoted and is not re-tested here.
* **Are file writing and editing reliable?** A closed heredoc always writes exactly the program, and targeted edits
  (`sed`) are rare. The weakness is not reliability but **feedback**: the observation after a write is the
  27-character empty acknowledgement, identical for every write. 69 of 77 identical rewrites follow it, and in 69
  of 77 the observation is byte-identical to the one before (pass 3 §2).
* **A correction to pass 3.** The pass-3 report said aci-v2's repeat guard "leaves the duplicate assistant message
  in the history". The traces show the opposite: the duplicate **was** removed (0 adjacent identical assistant
  messages remain in the four aci-v2 runs with guards). The loops persisted because each guard appended the **same**
  constant user note, so the history ended in a growing run of identical user messages (`…uuuuuuu`: up to 22
  guards in one run). The model re-proposed the same command each time. A constant message, removed or not, keeps
  the decisive suffix self-similar.
* **Are format-error retries useful?** They are partly useful: 52 runs recovered. Raising the retry count would
  only lengthen runs that are already looping (P(truncation | previous truncation) is 77%).

## 5. Budgets and termination (brief §5.3)

No trajectory in the 217 runs ends because of time (0 deadline exits; slowest 307 s), the request timeout,
context exhaustion, observation clipping, the container lifetime or the supervisor. The action limit ends 11 runs
(none after a public pass) and the repair limit ends 12, all with wrong algorithms. Raising these would add
attempts at already-failed programs, not solve tasks. **None is changed.**

**Output cap: where would more resources plausibly help?** Responses are bimodal:

* only **12** of 1,182 responses end between 3,000 and 4,095 tokens;
* **322** end exactly at the cap.

Truncated responses are runaway deliberation (a median of about 200 comment lines; pass 3 §1), not programs that
were nearly finished. A larger cap is therefore expected to help only if the deliberation converges within the
extra tokens. L3 tests exactly that, and its outcome measures say whether the extra tokens produced programs or
only more comments.

## 6. Agent versus model (brief §5.5)

The failure types are separated on the 8 development tasks (plan in `PREREGISTRATION.md`) by combining:

| Question | Evidence |
| --- | --- |
| Does Qwen lack the algorithm? | **one-shot probe** (`diagnostics/oneshot_probe.py`): one call, no agent, 8,192 tokens, frozen sampler. If it also fails, the method is missing. |
| Does it know a method but fail to express it as an action? | one-shot passes, agent A produces no program |
| Is it the prompt or interface? | L1 (reasoning step outside the protocol) and L3 (allowance) against `frozen-v6` |
| Context or budget? | §5: never binding |
| Wrong program? | hidden failure with a program; repair behaviour (L4) |

Results are in `LOCAL_AGENT_EXPERIMENTS.md` §5.

## 7. Correction from the pass-4 runs: context exhaustion does occur

§5 found context never binding in the 217 runs of passes 1–3 (largest prompt 13,825 tokens). The pass-4 runs found
**4 runs whose prompt reached the 16K window**:

* 3 C runs under the self-plan configuration, where the frontier plan, the self-plan and a long history add up;
* 1 E run under the original agent: the diagnosis-v2 probe at abc395_f, seed 2109, in a repeat loop of identical
  1,076-token responses.

**What happens at the limit.** The prompt for the next request was about 15.4–16.1K tokens, and Ollama 0.40.17
logged `chat prompt error … connection forcibly closed`. The frozen runtime has no history truncation, so
LiteLLM raises `APIConnectionError` and the runner records `infra_error`.

**Why it matters.** These failures are deterministic: the same seed reproduces the same context. They are agent
failures, not infrastructure, and rerunning them as "infrastructure" would hide a real cost. The measurement record
therefore derives `correctness.context_overflow` and excludes such runs from `infrastructure_failure`.

**Recommendation for the final study** (team decision): count a context overflow as a failed attempt, report it
separately, and keep the frozen 16K context. A configuration that adds context (such as `l1`) needs a larger window,
validated as its own change.
