# Lightweight evidence (committed)

| File | Contents |
| --- | --- |
| `selection.json` | Outcome-blind task selection (seed 2108; public metadata only) |
| `tasks-manifest.json` | Built tasks: public/hidden test **hashes**, counts and statement hashes (no test contents) |
| `FREEZE-mb.json` | Frozen mini-benchmark configuration: source commit, agent profile, prompt hashes, sha256 of every guidance artifact, task lists |
| `api-ledger.json` | Every paid request (reserved before sending): purpose, model, token usage, latency, finish reason, cost; plus the non-billable model metadata check |
| `guidance/<label>/*.json` | Every guidance artifact (plan/contract text, statement hash, prompt, provider, model, effort, Codex isolation evidence or API usage) |
| `plans/*.json` | Batch plans exactly as executed |
| `results/*.json`, `*.csv` | Per-attempt metrics per cohort (aggregate hidden pass counts only), `tables.md`, `cohorts.json` |
| `results/sensitivity.txt` | Tolerance / special-judge rechecks (`../diagnostics/`) |

Raw trajectories, candidate programs, hidden tests and Codex event streams stay outside Git under
`E:\CSC2108Local\reasoning-effectiveness` (`runs/`, `judge/hidden/`, `guidance/*/*.codex/`).
Reproduce the tables with `python -m guided_agent.report <study> <out> "MB1=mb1" ...`.
