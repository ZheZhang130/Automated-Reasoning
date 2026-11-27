# Enhanced D (contract) and E (diagnosis): sanitized development and validation results

This folder is exploratory development evidence. **It is not a benchmark.**

* **Source.** Exported from the study root `E:\CSC2108Local\enhanced-de-v2-study` by
  `python -m enhanced_de.export_sanitized`. `MANIFEST.json` lists every file with its sha256, and the privacy scan
  passed.
* **Findings and interpretation.** See `enhanced_de/docs/` (start with `04_RECOMMENDATIONS_AND_HANDOFF.md`).
* **Official benchmark.** It is in `results/final-main/` and is unchanged.

| Path | What it is |
| --- | --- |
| `reports/phase0_*.json` | Offline D2 mutant benchmark (18 consumed tasks, 96 references, 46 public-pass mutants), the pure-property ablation, and offline E2 review and strict checks |
| `reports/phase3_d2_provider_parity.json` | Four D2 banks authored through the paid API and compared with Codex banks |
| `reports/phase2_trigger_states_s2108.json` | Validation (test5_val16): the trigger states read from A's trajectories |
| `reports/phase2_composed_s2108.json` | Validation: per-arm, per-task outcomes. Cells an arm cannot reach are filled from A and labelled `from_A`; composed policies are labelled |
| `reports/process_v2.json` | Per-run process record for every live batch: trigger, delivery, program, length stops, tokens, wall time, hidden outcome, official-A comparison |
| `reports/reproducibility_v2.json` | Prompt, delivery-template and source hashes; caps; model identities |
| `batches/*.summary.json` | Per-batch summaries for phases 1A, 1B, 1C v1, 1C v2, Phase 2 and Phase 3 |
| `diagnoses/<batch>/<run>.diagnosis.json` | Every delivered or attempted E2 diagnosis: the evidence packet (public data only), the frontier response, the delivered message and the controller record |
| `d2_bundles/{codex,api}/*.bundle.json` | Authored D2 contracts and verification modules (statement-only). Materialized stress inputs are not exported |
| `guidance/test5-plans-codex/*.json` | Codex `plan-v1` artifacts for the 16 validation tasks (C and C-late) |
| `plans/*.json` | Official-runner plans: Phase 2 C and E-v1; the Phase 1B E-v1 control |
| `api-ledger.sanitized.json` | The paid-API ledger: 14 requests, $0.210 standard and $1.261 conservative |

**What is excluded.** Hidden tests and expected outputs; per-attempt trajectories; Ollama request and response logs;
agent containers; materialized D2 banks (about 91 MB of stress inputs); credentials.

* Hidden verdicts appear only as status, passed and total counts.
* Trajectories and logs remain in the study root on the reference host.

**Provider labels.**

* `codex-replay` is isolated Codex standing in for the frontier: free, and **not** API-equivalent.
* `openai-api` is the paid `gpt-6.2-sol`.

The two are never pooled in any table here.
