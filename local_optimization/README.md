# Frozen selector, judge monitor and research compatibility

This is **not just an archived study**: the public component uses `selected.py`, `optlib.py`, the configuration JSON and `judge_watch.py`. Use [python -m local_agent](../local_agent/README.md), not experimental drivers. The [dependency audit](../local_agent/dependencies.md#local_optimization) distinguishes active execution, test-only imports and compatibility-only code for every retained file.

| Important files | Role today |
| --- | --- |
| `selected.py`, `optlib.py` | Active source/image/profile verification, path helpers and dispatch to original v2 runtime |
| `final_selection.json`, `final_recommendation.json`, `profiles.json` | Active pins and recommendation; original control retained, challenger not promoted |
| `judge_watch.py` | Active independent judge launcher and owned-container resource evidence |
| `runtime_opt.py`, `transport.py`, `command_transport.py` | Alternative implementation used/imported by tests; not selected by the public baseline |
| `test_*.py`, split manifests, `check_*.py` | Unit/methodology tests and explicit Docker controls; some require historical E: artifacts |
| Remaining analysis, preparation, batch, diagnostic and report scripts | Hash-pinned research tooling; not invoked by public run/evaluate |

**Preserve every frozen file and path.** Selection verifies 38 file hashes, including inactive scripts. Do not edit expected hashes, rerun `freeze_final.py`, add Python modules to this historical collection, or invoke drivers to make the folder look current. The selector's historical `--challenger` option is not part of the public interface or recommended default.

Reports, aggregates and charts are in [evidence/local_optimization](../evidence/local_optimization/REPORT.md). Some scripts still reference former paths or can overwrite study outputs; historical reproduction needs the full archival context. [Results summary](../RESULTS_SUMMARY.md) explains the unpromoted challenger, and [project structure](../docs/PROJECT_STRUCTURE.md) describes optional future packaging without implementing it.
