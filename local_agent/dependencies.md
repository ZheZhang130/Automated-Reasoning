# Why the compatibility directories remain

The active path is:

```text
local_agent.cli
  → local_optimization/selected.py (unchanged subprocess)
    → optlib → local_eval_v2/common.py
    → local_eval_v2/runtime.py (unchanged subprocess, shared GPU lock)
      → local_baseline/runner.py → probe.py
      → mini-SWE-agent → LiteLLM → Ollama :11435
      → Docker public-only workspace

local_agent.cli evaluate (separate invocation)
  → local_optimization/judge_watch.py → optlib → common → runner
  → local_baseline/judge_lcb.py mounted into offline judge Docker
  → external pinned LiveCodeBench evaluator
```

`selected.py` verifies all 38 entries in `local_optimization/final_selection.json.runtime_sha256` before it selects the recommended original runtime. That historical integrity closure includes optimization drivers, transport alternatives, tests, baseline preparation/judging helpers and lockfiles that the default path does not otherwise execute. Removing those files would break the existing checks. They remain at their exact paths and measured bytes, with no bypass or replacement hashes. Only `heredoc-v6-16k-common` is exposed through the new entrypoint.

Existing unit tests also require `local_eval_v2/batch.py`, `analyze.py`, `validate_v5.py`, the optimization split manifests, `local_baseline/public_stdio_check.py` and synthetic fixture files. These are retained to exercise interruption/resume, accounting, sampler transport, containment and repair limits without launching a benchmark. Some frozen historical modules reference aggregate outputs at their old paths; the historical drivers are not supported active entrypoints. For historical reproduction use their complete archival checkout and external frozen source/archive. Evidence moved on this branch has an explicit path/hash map.

The old Git attributes stored `local_baseline/requirements.lock` with LF even though the measured working file and frozen SHA used CRLF. This branch stores the original measured CRLF bytes with `-text`; optimization files and evidence also use `-text` to prevent `core.autocrlf` from changing frozen bytes. The lock contents, packages, prompts and source behavior are unchanged. The source branch/worktree is untouched. New wrapper code uses LF.

Twenty-four unneeded historical Python/requirements files were removed from this branch's active tree, while their complete sources remain reachable in archival commits/tags. 102 report/data/chart files were relocated byte-for-byte under `evidence/`; configuration pins and split manifests needed by tests remain in place. `evidence/layout.json` records each former/new path, SHA256 and archive-only removal. Teammate orchestration/timeline files remain untouched.
