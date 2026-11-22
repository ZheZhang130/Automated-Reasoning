"""Deterministic, outcome-blind selection of the pass-3 extended cohort (public metadata and statements only).

Pool: AtCoder stdin tasks of the pinned test6 shard (``LCB_REVISION``; the newest official revision and shard
at selection time) that are not in the main 60-task manifest, not in the 75-ID scored union, not
teammate-used, and not used anywhere in pass 1 or pass 2.

Judge compatibility: ``output_semantics.classify`` on the public statement and sample outputs, overridden by
the manual review file. Only tasks whose decided category is ``exact`` are eligible; an unreviewed cue
excludes a task.

Order: lower public difficulty bands first (the contest letter is public metadata), because LiveCodeBench
labels every remaining task "hard":
  band 1 = ABC D/E, band 2 = ABC F, band 3 = ARC A/B, band 4 = ABC G and ARC C or later.
Within a band the order is sha256(seed:pass3:band:task_id). The first ``n`` tasks form the cohort; the frozen
order also defines any predeclared reduction of a second-seed matrix (a prefix of complete task blocks).
"""
import hashlib
import json
from pathlib import Path

from . import output_semantics
from .common import normalize_task_id, sha256_file, utc_now, write_json
from .selection import SEED, TEAMMATE_USED
from .selection_pass2 import PASS1_USED
from .tasks import exclusion_union, manifest_entries, rows_by_id

PASS2_USED = {'lcb-atcoder-' + t for t in ('abc394_b', 'abc399_f', 'abc398_d', 'abc388_e', 'abc396_f')}
SALT = 'pass3'


def band(task_id):
    contest, letter = task_id.split('-')[-1].split('_')
    if contest.startswith('abc'):
        return {'d': 1, 'e': 1, 'f': 2}.get(letter, 4 if letter >= 'g' else 0)
    if contest.startswith('arc'):
        return 3 if letter in ('a', 'b') else 4
    return 5


def key(task_id):
    return band(task_id), hashlib.sha256(f'{SEED}:{SALT}:{band(task_id)}:{task_id}'.encode()).hexdigest()


def pool(shard, review_path):
    rows = rows_by_id(shard)
    manifests = manifest_entries()
    scored = exclusion_union()
    reviews = output_semantics.load_review(review_path)
    main = {t for t, e in manifests.items() if e['manifest'] == 'main'}
    used = TEAMMATE_USED | PASS1_USED | PASS2_USED
    candidates, excluded = {}, []
    for task_id, row in sorted(rows.items()):
        if row['platform'] != 'atcoder' or task_id in main or task_id in used or normalize_task_id(task_id) in scored:
            continue
        samples = [c['output'] for c in json.loads(row['public_test_cases'])]
        auto = output_semantics.classify(row['question_content'], samples)
        category, how = output_semantics.decide(task_id, auto, reviews)
        entry = {'task_id': task_id, 'difficulty': row['difficulty'], 'title': row['question_title'],
                 'contest_date': row['contest_date'][:10], 'manifest': manifests.get(task_id, {}).get('manifest'),
                 'band': band(task_id), 'output_category': category, 'decided_by': how,
                 'auto_signals': auto['signals']}
        if output_semantics.eligible_for_judge_0_2_1(category):
            candidates[task_id] = entry
        else:
            excluded.append(entry)
    return candidates, excluded


def select(shard, review_path, n=12):
    candidates, excluded = pool(shard, review_path)
    ordered = sorted(candidates, key=key)
    chosen = ordered[:n]
    return {'created_utc': utc_now(), 'seed': SEED, 'salt': SALT, 'shard': 'test6.jsonl',
            'shard_sha256': sha256_file(shard), 'review_sha256': sha256_file(review_path),
            'rule': __doc__.strip(), 'n_requested': n,
            'pool_size': len(candidates), 'pool_by_band': {b: sum(1 for t in candidates.values() if t['band'] == b)
                                                            for b in (1, 2, 3, 4)},
            'excluded_output_semantics': excluded,
            'frozen_order': [candidates[t] for t in chosen],
            'not_selected': [candidates[t]['task_id'] for t in ordered[n:]]}


if __name__ == '__main__':
    import sys
    result = select(Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[4]) if len(sys.argv) > 4 else 12)
    write_json(Path(sys.argv[3]), result)
    print(json.dumps({'pool_by_band': result['pool_by_band'], 'excluded': [e['task_id'] for e in
                      result['excluded_output_semantics']],
                      'cohort': [f"{t['task_id']} band{t['band']}" for t in result['frozen_order']]}, indent=1))
