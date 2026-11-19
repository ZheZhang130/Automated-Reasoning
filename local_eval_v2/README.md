# Original agent runtime and retained evaluation support

The final component **actively uses `runtime.py` here**. Windows invokes its original CLI through the frozen selector; portable Mac execution reuses its original run bytecode/classes with separate host bindings. Use the [public CLI](../local_agent/README.md), which supplies identity checks and the result contract. See [project structure](../docs/PROJECT_STRUCTURE.md), [Mac setup](../docs/MACOS.md) and the [file audit](../local_agent/dependencies.md#local_eval_v2).

| Important files | Role today |
| --- | --- |
| `runtime.py` | Original prompts, text-model agent, public-test hooks and trajectory/usage recording |
| `common.py` | Shared E: paths, baseline import lookup, serialization/hashing and Windows GPU lock |
| `profiles.json` | Active `heredoc-v6-16k-common` settings alongside historical profiles |
| `public_check.py` | Frozen checker template; actual runs execute the trusted bundle's `check.py` |
| `dataset.py` | Frozen historical dataset helper, imported for constants by test-support code; not a public-path downloader |
| `batch.py`, `analyze.py`, `validate_v5.py` | Historical evaluation/report/control code retained for tests; not current task entrypoints |
| `test_v2.py`, `test_wire.py`, `test_interruption.py`, `test_analysis.py` | Scheduling, submission, adapter, interruption and accounting tests |
| `judge.Dockerfile` | Historical v2 recipe layering a deadline on v1; not built during tasks |

**Do not edit source-pinned runtime, prompts, profiles, shared helpers or checker.** Do not launch old batch/download/development paths for normal integration. Running `validate_v5.py` directly also executes Docker/evaluator controls; importing its `Hooks` tests is different. Current supported judging uses `local_optimization/judge_watch.py`, not the legacy `pilot.score` imported by some tests.

The completed three-model study is in [the evidence report](../evidence/local_eval_v2/RESULTS.md), with provenance/aggregates indexed [here](../evidence/README.md). Historical reproduction needs the archive and external E: source/data context; this folder's name does not authorize new benchmark runs.
