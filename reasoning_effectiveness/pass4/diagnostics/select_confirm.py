"""Outcome-blind pass-4 confirmation cohort: the test6 tasks never used by the project, by the pass-3 rule.

usage: python reasoning_effectiveness/pass4/diagnostics/select_confirm.py SHARD REVIEW OUT.json [N]

Pool = ``selection_pass3.pool`` (AtCoder stdin, not in the main manifest, not in the 75-ID union, not teammate- or
pass-1/2-used, judge-exact only) minus every task of the pass-3 cohort and its not-selected order (all were consumed
or ranked in pass 3), minus anything used in pass 4. Order: pass-3 band key with salt ``pass4-confirm``. These tasks
are not part of the planned final benchmark (main 60 + test5).
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from guided_agent import selection_pass3  # noqa: E402
from guided_agent.common import sha256_file, utc_now, write_json  # noqa: E402

SALT = 'pass4-confirm'


def key(task_id):
    band = selection_pass3.band(task_id)
    return band, hashlib.sha256(f'{selection_pass3.SEED}:{SALT}:{band}:{task_id}'.encode()).hexdigest()


def main(shard, review, out, n=8):
    candidates, excluded = selection_pass3.pool(Path(shard), Path(review))
    p3 = json.loads((ROOT / 'reasoning_effectiveness/pass3/evidence/selection-pass3.json').read_text(encoding='utf-8'))
    used = {t['task_id'] for t in p3['frozen_order']}
    used |= {'lcb-atcoder-' + t for t in ('abc400_b', 'abc393_d', 'arc195_a', 'abc398_d', 'abc388_e', 'abc389_f',
                                           'abc397_f', 'arc192_a', 'abc390_c', 'abc390_f', 'abc395_f', 'abc388_f',
                                           'arc190_c', 'arc193_a', 'abc391_f', 'arc195_d', 'abc397_e', 'arc193_b',
                                           'arc194_e')}
    remaining = sorted((t for t in candidates if t not in used), key=key)
    chosen = remaining[:int(n)]
    result = {'created_utc': utc_now(), 'rule': __doc__.strip(), 'shard_sha256': sha256_file(shard),
              'review_sha256': sha256_file(review), 'pool_after_exclusions': len(remaining),
              'frozen_order': [candidates[t] for t in chosen], 'not_selected': remaining[int(n):]}
    write_json(Path(out), result)
    print(json.dumps({'pool': len(remaining), 'chosen': [f"{t} band{candidates[t]['band']} {candidates[t]['difficulty']}"
                                                         for t in chosen], 'rest': remaining[int(n):]}, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:])
