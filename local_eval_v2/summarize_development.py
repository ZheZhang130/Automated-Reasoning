"""Export development-only evidence; never reads the evaluation task bundles."""
import csv
from common import DATA, ROOT, read, save


def main():
    roots = [DATA / 'development-v5-experiments', DATA / 'development-secondary', DATA / 'development-common-v6']
    rows = []
    for root in roots:
        for path in sorted(root.glob('*/development-result.json')):
            item = read(path)
            rows.append({k: item.get(k) for k in ('model', 'profile', 'task_id', 'status', 'seconds', 'actions', 'repairs', 'format_errors', 'run')} |
                        {'official': item['evaluation']['status'], 'action_limit': item.get('actions_limit', 20)})
    with (ROOT / 'development_metrics.csv').open('w', encoding='utf-8', newline='') as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines = ['# Development evidence', '',
             f'{len(rows)} finalized development runs, on four synthetic tasks only. These are configuration diagnostics and are excluded from benchmark accuracy. The development tasks test negative-integer aggregation repair, delimiter validation, ASCII case conversion, and a functional distinct-count interface. All held-out development judging remains separate from the model.', '',
             'The earlier three-task v4 prototype has nine completed records plus a preserved partial attempt under `E:\\CSC2108Local\\eval-v2\\development-experiments`. Its interface was revised before v5; do not pool those trials with v5. Each completed v5/secondary run retains its exact configuration, source hashes and full trajectory. Native v5 initially reused fenced text examples; corrected native v6 uses tool-only instructions, and is the native comparison used for the decision.', '',
             '## Per-run outcomes', '',
             '| Model | Profile | Task | Action limit | Official result | Stop | Seconds | Actions | Repairs | Format errors |',
             '| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |']
    for r in rows:
        lines.append(f"| {r['model']} | {r['profile']} | {r['task_id']} | {r['action_limit']} | {r['official']} | {r['status']} | {r['seconds']:.3f} | {r['actions']} | {r['repairs']} | {r['format_errors']} |")
    lines += ['', '## Context allocation probes', '',
              'Nine short-prompt allocation probes use the same hardware. Reported model allocation and GPU allocation are Ollama snapshots, not process peak memory. A short probe does not exercise the full context window.', '',
              '| Model | Context | Seconds | Model bytes | GPU bytes | CPU offload bytes |',
              '| --- | ---: | ---: | ---: | ---: | ---: |']
    for r in read(DATA / 'development-experiments/memory.json'):
        m = r['loaded']['models'][0]
        lines.append(f"| {r['model']} | {r['context']} | {r['elapsed_seconds']:.3f} | {m['size']} | {m['size_vram']} | {m['size']-m['size_vram']} |")
    lines += ['', '## Long-input stress probes', '',
              'The inert prompt is about 20K tokens, with a 32-token output ceiling. Smaller windows truncate deliberately. Prompt token counts below are raw Ollama values; allocation is the requested context. This does not measure coding capability. Some probes hit the deliberately tiny output limit. The initial 7B/16K request returned HTTP 500; it was not recorded as a successful row and its successful retry is listed here. The failed command/traceback remains in the session history; no failure body was captured by the original helper.', '',
              '| Model | Context | Prompt eval tokens | Seconds | Done reason |',
              '| --- | ---: | ---: | ---: | --- |']
    for r in read(DATA / 'development-experiments/stress.json'):
        lines.append(f"| {r['model']} | {r['context']} | {r['response'].get('prompt_eval_count')} | {r['elapsed_seconds']:.3f} | {r['response'].get('done_reason')} |")
    lines += ['', '## Decision and limits', '',
              'The common 16K text workflow passed 4/4 (9B), 3/4 (14B), and 2/4 (7B) at both temperatures 0 and 0.2. The four-task sample is too small for a statistical configuration claim. The 14B and 7B negative-squares failures persisted at 40 actions/5 repairs; their repeated identical/wrong code does not automatically count as multiple repair cycles. Corrected native v6 worked for 9B but both Qwen2.5 models emitted no native action. Qwen3.5 thinking-on passed 4/4 but was slower than thinking-off on these easy tasks. It was not silently enabled in the primary benchmark.', '',
              'The 32K 14B model allocation offloaded 1,131,497,389 bytes in the allocation probe and the long-input run was much slower. 16K was chosen as a common GPU-resident allocation, not an assertion that no long trajectory can exhaust it. Raw context logs and length-limit reasons are retained in every main run. See DECISION.md for the pre-benchmark freeze.', '',
              'The final 12 v6 trials explicitly harmonize native Ollama sampler options and verify each actual request body. They passed 4/4, 3/4 and 2/4 (9B, 14B, 7B), matching the observed small-set correctness with tag defaults. They are separate from the earlier v5 trials. The v6 correction followed a model-metadata audit during an initial benchmark batch; that batch stopped at 111 and is retained separately, not pooled into primary v6 results. See DECISION.md.', '',
              'Artifacts: `E:\\CSC2108Local\\eval-v2\\development-v5-experiments`, `development-secondary`, `development-common-v6`, and `development-experiments/{memory,stress}.json`. `development_metrics.csv` exports numerical outcomes without candidate source or held-out cases.']
    (ROOT / 'DEVELOPMENT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    save(DATA / 'development-summary.json', {'finalized_development_runs': len(rows), 'prototype_completed': 9,
                                           'memory_probes': 9, 'successful_stress_probes': 9,
                                           'initial_stress_http500': 1})
    print({'development_runs': len(rows)})


if __name__ == '__main__':
    main()
