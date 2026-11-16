# Configuration decision history

**Active primary profile: `heredoc-v6-16k-common`.** The v5 decision below is preserved as history and was superseded by the explicit sampler correction documented at the end.

## Initial v5 decision

Frozen after development and before any of the 24 selected benchmark tasks ran.

Use `heredoc-v5-16k-t02` for all three models: text actions, literal heredoc instructions, 16,384 context tokens, 4,096 generated tokens per response, temperature 0.2, seeds 2108/2109 for repetitions 1/2, 20 executed actions, 3 repair cycles and 600 seconds. Qwen3.5 thinking is disabled; the Qwen2.5 models do not expose that setting.

The common development set has four synthetic tasks, including stdin and functional interfaces, and is separate from LiveCodeBench. At both temperature 0 and 0.2, Qwen3.5 passed 4/4, Qwen2.5-Coder 14B passed 3/4 and 7B passed 2/4. Temperature 0.2 preserves the observed development correctness while allowing variation between seeded attempts. This small sample does not establish an optimal temperature.

16K fits all three models wholly in GPU allocation snapshots. The 14B 32K allocation offloads about 1.13 GB and its long-input probe took 78.5 seconds versus 13.0 at 16K. Long inputs deliberately overflow the smaller windows; these probes are stress diagnostics, not coding accuracy tests. One initial 7B 16K stress request returned HTTP 500; the retry succeeded. Preserve that failure in the development record.

Increasing the negative-squares task to 40 actions/5 repairs did not change correctness for any model. Corrected native-tool instructions passed that task for 9B, while both Qwen2.5 models produced three format failures without executing actions. Native tools therefore do not provide a reliable common workflow here. Qwen3.5 thinking enabled passed the same four development tasks but took longer than thinking disabled; it remains a separately labeled secondary experiment.

No benchmark correctness outcome informed this choice. Configuration changes after the batch starts require a new batch, rather than changing the frozen comparison.

## Corrected common-sampler primary configuration

After 109 v5 runs, inspection of model metadata revealed unequal inherited sampler settings. Qwen3.5 declares presence penalty 1.5, top-k 20 and top-p 0.95; the Qwen2.5 tags declare no corresponding overrides. Shared client kwargs therefore did not fully harmonize sampling. The v5 batch stopped at the next completed-run boundary, at 111/144. Its plan, raw artifacts and original source hashes are preserved separately; all 111 completed runs were verified against their original source hashes. Those results are not pooled into the primary comparison.

The corrected v6 profile keeps the same prompt, tasks, context, output ceiling, temperature, seeds and execution budgets. It explicitly sends these identical Ollama options for every model: top-k 40, top-p 0.9, min-p 0, repeat penalty 1.0, repeat-last-n 64, presence penalty 0 and frequency penalty 0. Penalties are neutral, rather than inheriting model-tag overrides. This is a configuration-integrity correction based on metadata, not solution-specific tuning. The tasks have already been run in the superseded experiment; they are not described as newly unseen in v6. Models are stateless between attempts, weights are unchanged, and no prior candidate or private feedback is supplied to them.

LiteLLM 1.81.16 maps its OpenAI-style frequency penalty to an Ollama repeat penalty, and filters unsupported OpenAI parameters. V6 supplies a complete native `options` block through `extra_body`, captures actual outgoing requests, and verifies exact values. A mocked transport test exercises the real adapter without inference; all 12 real development trials verified their wire payloads. Correctness remained 4/4, 3/4 and 2/4 for 9B, 14B and 7B. The source/configuration is frozen again in a NEW batch before v6 benchmark inference. Raw v5 results are retained in `TAG_DEFAULT_RESULTS.md` and on E:.
