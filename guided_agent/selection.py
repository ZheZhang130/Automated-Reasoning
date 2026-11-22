"""Deterministic, outcome-blind task selection for the reasoning-effectiveness pass.

Only public metadata (platform, LiveCodeBench difficulty label, contest/problem letter,
manifest membership, earlier-use lists) is read. Hidden tests, reference solutions and
any model outcome on candidate tasks are never consulted. Order within a stratum is
sha256(seed:task_id), so the selection is reproducible on any host.
"""
import hashlib
import json
from pathlib import Path

from .common import normalize_task_id, sha256_file, utc_now, write_json
from .tasks import exclusion_union, manifest_entries, rows_by_id

SEED = 2108
TEAMMATE_USED = {'lcb-atcoder-abc393_a'}  # orchestration smoke run (orchestration/runs/…)


def order(ids, salt):
    return sorted(ids, key=lambda t: hashlib.sha256(f'{SEED}:{salt}:{t}'.encode()).hexdigest())


def letter(task_id):
    return task_id.rsplit('_', 1)[-1]


def select(shard):
    rows = rows_by_id(shard)
    manifests = manifest_entries()
    scored = exclusion_union()
    atcoder = {t: r for t, r in rows.items() if r['platform'] == 'atcoder'}
    main = {t for t, e in manifests.items() if e['manifest'] == 'main'}
    used = {t for t in atcoder if normalize_task_id(t) in scored} | TEAMMATE_USED

    def pool(difficulty, *, fresh):
        return [t for t, r in atcoder.items() if r['difficulty'] == difficulty and t not in main
                and ((t not in used) if fresh else (t in used))]

    # Development: already-scored / teammate-used tasks outside the main cohort (consumes nothing fresh).
    dev = order(pool('easy', fresh=False), 'dev-easy')[:2] + order(pool('medium', fresh=False), 'dev-medium')[:2]
    taken = set(dev)
    mb1 = (order(pool('easy', fresh=True), 'mb1-easy')[:1] + order(pool('medium', fresh=True), 'mb1-medium')[:4]
           + order(pool('hard', fresh=True), 'mb1-hard')[:1])
    taken |= set(mb1)
    # No fresh medium task remains; use ABC D/E problems labelled hard (lowest public difficulty band left).
    lower_hard = [t for t in pool('hard', fresh=True) if t not in taken and t.split('-')[-1].startswith('abc')
                  and letter(t) in ('d', 'e')]
    mb2 = order(lower_hard, 'mb2-lower-hard')[:4]
    remaining = {d: len([t for t in pool(d, fresh=True) if t not in taken | set(mb2)]) for d in ('easy', 'medium', 'hard')}

    def describe(ids):
        return [{'task_id': t, 'difficulty': atcoder[t]['difficulty'], 'title': atcoder[t]['question_title'],
                 'manifest': manifests.get(t, {}).get('manifest'), 'previously_scored_or_used': t in used} for t in ids]

    return {'created_utc': utc_now(), 'seed': SEED, 'shard_sha256': sha256_file(shard),
            'rule': {'development': 'previously scored/teammate-used AtCoder tasks outside the main manifest; '
                                    '2 easy + 2 medium by seeded hash order',
                     'mini_benchmark_1': 'fresh (not in main manifest, not in 75-ID union, not teammate-used, '
                                         'not development); 1 easy + 4 medium + 1 hard by seeded hash order',
                     'mini_benchmark_2': 'fresh and unused by MB1; ABC problems D/E labelled hard (no fresh '
                                         'medium remains); 4 by seeded hash order'},
            'excluded_union_size': len(scored), 'main_manifest_size': len(main),
            'development': describe(dev), 'mini_benchmark_1': describe(mb1), 'mini_benchmark_2': describe(mb2),
            'fresh_remaining_after_selection': remaining}


if __name__ == '__main__':
    import sys
    result = select(Path(sys.argv[1]))
    write_json(Path(sys.argv[2]), result)
    print(json.dumps({k: [t['task_id'] + ':' + t['difficulty'] for t in result[k]]
                      for k in ('development', 'mini_benchmark_1', 'mini_benchmark_2')}, indent=1))
