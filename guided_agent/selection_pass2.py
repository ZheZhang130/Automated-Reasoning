"""Deterministic, outcome-blind selection of the pass-2 validation cohort (public metadata only).

Eligible: AtCoder stdin tasks in the pinned test6 shard that are not in the main 60-task manifest, not in
the 75-ID scored union, not teammate-used, and not used anywhere in pass 1 (development, MB1, MB2).
Tasks whose public statement admits tolerance-based or multiple valid outputs are excluded because judge
0.2.1 compares outputs exactly (pass-1 finding); the rule reads only the statement text. Order within a
difficulty stratum is sha256(seed:salt:task_id).
"""
import json
import re
from pathlib import Path

from .common import normalize_task_id, sha256_file, utc_now, write_json
from .selection import SEED, TEAMMATE_USED, order
from .tasks import exclusion_union, manifest_entries, rows_by_id

PASS1_USED = {'lcb-atcoder-' + t for t in (
    'abc391_a', 'abc400_b', 'arc195_a', 'arc192_a',                                  # development
    'abc396_a', 'abc392_d', 'abc390_c', 'abc396_d', 'abc394_c', 'abc388_g',          # mini-benchmark 1
    'abc393_d', 'abc396_e', 'abc393_e', 'abc391_e')}                                 # mini-benchmark 2
UNSUPPORTED_OUTPUT = re.compile(
    r'absolute or relative error|relative or absolute error|absolute error|relative error|error (?:is )?at most|'
    r'within an? (?:absolute|relative)?\s*error|if there are multiple|multiple (?:valid |correct )?(?:answers|solutions)|'
    r'any of them|print any|output any|may print any|any (?:such|valid|correct) ', re.I)


def eligible(shard):
    rows = rows_by_id(shard)
    manifests = manifest_entries()
    scored = exclusion_union()
    main = {t for t, e in manifests.items() if e['manifest'] == 'main'}
    out, excluded_output = {}, []
    for task_id, row in rows.items():
        if row['platform'] != 'atcoder' or task_id in main or task_id in TEAMMATE_USED or task_id in PASS1_USED:
            continue
        if normalize_task_id(task_id) in scored:
            continue
        if UNSUPPORTED_OUTPUT.search(row['question_content']):
            excluded_output.append(task_id)
            continue
        out[task_id] = row
    return out, sorted(excluded_output), manifests


def confirmation_pool(shard):
    """Previously scored by the EARLIER evaluator (75-ID union) but outside the main manifest, unused in pass 1
    and unseen by any pass-2 tuning. Not fresh for the local model's history; labelled 'confirmation'."""
    rows = rows_by_id(shard)
    manifests = manifest_entries()
    scored = exclusion_union()
    main = {t for t, e in manifests.items() if e['manifest'] == 'main'}
    return {t: r for t, r in rows.items() if r['platform'] == 'atcoder' and t not in main and t not in TEAMMATE_USED
            and t not in PASS1_USED and normalize_task_id(t) in scored
            and not UNSUPPORTED_OUTPUT.search(r['question_content'])}, manifests


def select(shard, n_fresh_hard=4, n_confirm_medium=3):
    pool, excluded_output, manifests = eligible(shard)
    by = {d: [t for t, r in pool.items() if r['difficulty'] == d] for d in ('easy', 'medium', 'hard')}
    # Fresh stratum: the one fresh easy task, then the lowest public difficulty band left (ABC hard D-F).
    lower_hard = [t for t in by['hard'] if t.split('-')[-1].startswith('abc') and t.rsplit('_', 1)[-1] in ('d', 'e', 'f')]
    fresh = order(by['easy'], 'pass2-easy')[:1] + order(by['medium'], 'pass2-medium')[:2] + \
        order(lower_hard, 'pass2-lower-hard')[:n_fresh_hard]
    confirm_rows, _ = confirmation_pool(shard)
    confirm_medium = [t for t, r in confirm_rows.items() if r['difficulty'] == 'medium']
    confirm = order(confirm_medium, 'pass2-confirm-medium')[:n_confirm_medium]

    def describe(ids, rows, stratum):
        return [{'task_id': t, 'difficulty': rows[t]['difficulty'], 'title': rows[t]['question_title'],
                 'manifest': manifests.get(t, {}).get('manifest'), 'stratum': stratum} for t in ids]

    return {'created_utc': utc_now(), 'seed': SEED, 'shard_sha256': sha256_file(shard),
            'rule': __doc__.strip() + '\nConfirmation stratum: ' + confirmation_pool.__doc__.strip(),
            'pool_sizes': {d: len(v) for d, v in by.items()},
            'confirmation_pool_medium': len(confirm_medium),
            'excluded_unsupported_output': excluded_output,
            'validation': describe(fresh, pool, 'fresh') + describe(confirm, confirm_rows, 'confirmation')}


if __name__ == '__main__':
    import sys
    result = select(Path(sys.argv[1]))
    write_json(Path(sys.argv[2]), result)
    print(json.dumps({k: result[k] for k in ('pool_sizes', 'validation')}, indent=1))
    print('excluded for output type:', len(result['excluded_unsupported_output']))
