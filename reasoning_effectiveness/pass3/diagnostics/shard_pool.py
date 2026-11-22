"""Count candidate tasks per LiveCodeBench shard for final-benchmark planning (public metadata and statements).

usage (repository root):  python -m reasoning_effectiveness.pass3.diagnostics.shard_pool OUT.json SHARD.jsonl ...

Per shard: platform x difficulty counts, AtCoder contest-date range, the output-semantics cue counts from
``guided_agent.output_semantics.classify`` (cues need a manual review before use), and the number of tasks
already used by this project (main/pilot manifests, 75-ID union, passes 1-3). Hidden tests are decoded only
to count hidden files (dataset structure), never inspected.
"""
import json
import sys
from collections import Counter
from pathlib import Path

from guided_agent import output_semantics
from guided_agent.common import normalize_task_id
from guided_agent.selection import TEAMMATE_USED
from guided_agent.selection_pass2 import PASS1_USED
from guided_agent.selection_pass3 import PASS2_USED
from guided_agent.tasks import build_data_module, exclusion_union, manifest_entries


def main(out, *shards):
    bd = build_data_module()
    manifests = manifest_entries()
    union = exclusion_union()
    used = TEAMMATE_USED | PASS1_USED | PASS2_USED | set(manifests)
    pass3 = {'lcb-atcoder-' + t for t in ('abc397_e', 'abc388_f', 'abc395_f', 'abc389_f', 'abc397_f', 'abc391_f',
                                          'abc390_f', 'arc193_a', 'arc193_b', 'arc195_d', 'arc194_e', 'arc190_c')}
    report = {}
    for shard in map(Path, shards):
        counts, cues, dates, hidden_small, used_here = Counter(), Counter(), [], 0, Counter()
        with shard.open(encoding='utf-8') as stream:
            for line in stream:
                row = json.loads(line)
                task_id = f"lcb-{row['platform']}-{row['question_id']}"
                counts[f"{row['platform']}/{row['difficulty']}"] += 1
                if row['platform'] != 'atcoder':
                    continue
                dates.append(row['contest_date'][:10])
                public = json.loads(row['public_test_cases'])
                auto = output_semantics.classify(row['question_content'], [c['output'] for c in public])
                cues[auto['auto_category'] if auto['needs_review'] else 'no_cue'] += 1
                try:
                    if len(bd.decode_private(row['private_test_cases'])) < 5:
                        hidden_small += 1
                except Exception:
                    hidden_small += 1
                if task_id in used or normalize_task_id(task_id) in union or task_id in pass3:
                    used_here[row['difficulty']] += 1
        report[shard.name] = {'counts': dict(counts), 'atcoder_dates': [min(dates), max(dates)] if dates else None,
                              'atcoder_output_cues': dict(cues), 'atcoder_with_fewer_than_5_hidden_files': hidden_small,
                              'atcoder_already_used_by_project': dict(used_here)}
        print(shard.name, json.dumps(report[shard.name]))
    Path(out).write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:])
