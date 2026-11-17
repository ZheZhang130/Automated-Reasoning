# Delivery prompt diagnostic

One diagnostic validation on four fresh tasks (one easy, three medium), comparing original agent A, prompt-only A2 and original one-shot B. This is not another optimization search. Use the existing branch; no push or merge.

Phase 1 (`forensics.py`) reads only the previous ablation's saved outputs and public feedback. It makes no model calls and never inspects private test contents/official solutions. `FORENSICS.md` cites exact response and trajectory indices. The observed issue is reasoning commentary inside unclosed source-writing commands, rather than prose before the command fence. Repeated identical rewrites after recognized public failure explain another failure; no repair-accounting fix is applied.

**Only experimental change:** A2 replaces the system prompt, as one indivisible factor. `pilot_common.py` contains the complete prompt. Everything else reuses the previous worker: mini-SWE-agent, shell execution, persistent workspace, action parser, rejection of partial commands, sampler, context/output/thinking settings, seed, 120-second outer cap, 10 actions/3 repairs, finalization reserve, public checker and independent official evaluator. One-shot output is never supplied to either agent. A2's protocol sidecar distinguishes it from the original worker's generic raw `condition=A` field.

The controller reuses the previous owned-process/container supervisor, GPU lock and 35-minute hard ceiling (25-second shutdown reserve). The single timer includes CPU parser/sandbox controls, two actual A2 synthetic fixtures, all 12 benchmark attempts, judging and cleanup. No resume/timer reset, repeated task attempts or tuning on validation results. Interrupted model replies retain unknown token bounds; incomplete judging is never scored as an incorrect solution.

CPU controls verify strict malformed-fence rejection, Docker security settings, genuine shell execution, complete file writing, persistent workspace, visible failure, a changed repair followed by success and submission. The corrected program used in this synthetic backend control is a pre-existing Qwen synthetic fixture, not a benchmark or one-shot solution. Two separate A2 model fixtures cover stdin/stdout and functional interfaces and must pass visible feedback and independent judging before validation starts.

Artifact root: `E:\CSC2108Local\agent-delivery-pilot`. Existing baseline, eval-v2, optimization and one-shot sources/results stay unchanged. Code and metadata only are committed; full prompts, responses, candidates, trajectories, private rows and judge logs remain on E:.

From repository root (PowerShell):

```powershell
. .\local_baseline\env.ps1
$deliveryPython = 'E:\CSC2108Local\.venv\Scripts\python.exe'
& $deliveryPython agent_delivery_pilot\forensics.py  # No inference
& $deliveryPython agent_delivery_pilot\prepare.py    # Freeze four tasks once
& $deliveryPython agent_delivery_pilot\run.py        # One bounded execution
& $deliveryPython agent_delivery_pilot\report.py     # Read-only analysis
```

Never rerun the measured pilot or reset its timer. `future_exclusions.json` records the old 71 IDs plus these four tasks. Final interpretation distinguishes delivery, implementation correctness and genuine test-driven recovery; faster commands alone do not prove stronger algorithms.
