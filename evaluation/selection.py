"""Deterministic, outcome-blind benchmark selection from the pinned LiveCodeBench shard.

Only public metadata is read to *choose* tasks: platform, LiveCodeBench difficulty label, contest, hidden-test
*count*, the output-semantics audit (public statements) and the exposure registry. Hidden test contents, reference
solutions and model outcomes are never consulted. Test hashes are computed afterwards, for the manifest only.

Eligibility (every reason is recorded):

* AtCoder stdin task of the pinned shard (judge 0.2.1 judges stdin/stdout only; LeetCode tasks are functional);
* output semantics ``exact`` in ``evaluation/data/output-semantics-audit.json`` (no tolerance, multiple-answer,
  case-insensitive or interactive task: exact comparison would give false negatives, and relaxing the comparison
  globally would give false positives elsewhere);
* at least ``min_hidden_tests`` hidden tests (default 40);
* not in a reserved manifest (default ``judge/manifests/pilot.json``, kept for smoke tests);
* optionally (``exclude_previously_used``) no recorded historical exposure (classes development, selection_holdout,
  other_scored and uncertain are all excluded).

Order: explicit ``tasks`` first; then, with a ``base`` manifest, its eligible members in base order (ineligible ones are
listed as removed, with reasons), each removed one replaced from its own (difficulty, contest series) stratum when
possible; then the remaining quota by ``sha256(seed:salt:difficulty:task_id)``. With ``prefer_unexposed``, candidates
without recorded exposure come first within each stratum (then the same sha256 order); exposed tasks stay eligible.
A quota the eligible pool cannot fill is an error that reports the available counts; nothing is silently reduced.
"""
import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path

from . import exposure as exposurelib
from .tasks import REPO, SHARD, _LFPath, build_data, read_json, sha256_file, write_json

AUDIT = REPO / 'evaluation/data/output-semantics-audit.json'
RESERVED = (REPO / 'judge/manifests/pilot.json',)
DIFFICULTIES = ('easy', 'medium', 'hard')
SALT = 'final-v1'


class InsufficientPool(ValueError):
    def __init__(self, message, available):
        super().__init__(message)
        self.available = available


def series(task_id):
    return task_id.split('-')[-1][:3]


def load_pool(shard):
    """task_id -> public metadata (and the row, for hashing later) of every AtCoder stdin task in the shard."""
    bd = build_data()
    pool = {}
    with Path(shard).open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            if row['platform'] != 'atcoder':
                continue
            public = json.loads(row['public_test_cases'])
            hidden = bd.decode_private(row['private_test_cases'])   # counted only, never read
            if {c.get('testtype') for c in public + hidden} != {'stdin'}:
                continue
            task_id = f"lcb-{row['platform']}-{row['question_id']}"
            pool[task_id] = {'task_id': task_id, 'difficulty': row['difficulty'], 'title': row['question_title'],
                             'contest_id': row['contest_id'], 'contest_date': row['contest_date'],
                             'n_public': len(public), 'n_hidden': len(hidden), 'series': series(task_id),
                             '_row': row}
    return pool


def reasons(info, *, audit, reserved, registry, min_hidden_tests, exclude_previously_used):
    out = []
    semantics = (audit['tasks'].get(info['task_id']) or {}).get('category', 'unreviewed')
    if semantics != 'exact':
        out.append(f'output semantics: {semantics}')
    if info['n_hidden'] < min_hidden_tests:
        out.append(f"{info['n_hidden']} hidden tests < {min_hidden_tests}")
    if info['task_id'] in reserved:
        out.append(f"reserved by {reserved[info['task_id']]}")
    if exclude_previously_used:
        cls = exposurelib.classify(info['task_id'], registry)['class']
        if cls != 'none_known':
            out.append(f'previously used ({cls})')
    return out


def _reason_key(reason):
    """'output semantics: tolerance' -> 'output semantics: tolerance'; '4 hidden tests < 40' -> 'hidden tests < 40'."""
    if 'hidden tests <' in reason:
        return 'hidden tests < ' + reason.rsplit('<', 1)[1].strip()
    return reason.split(' (')[0] if reason.startswith('previously used') else reason


def _order(ids, seed, difficulty):
    return sorted(ids, key=lambda t: hashlib.sha256(f'{seed}:{SALT}:{difficulty}:{t}'.encode()).hexdigest())


def select(pool, *, counts=None, tasks=(), base=None, seed=2108, min_hidden_tests=40, exclude_previously_used=False,
           prefer_unexposed=False, reserved_manifests=RESERVED, audit=None, registry=None):
    """Returns {'selected': [task_id...], 'removed': [...], 'replacements': [...], 'eligible_counts': {...}}."""
    audit = audit or read_json(AUDIT)
    registry = registry or exposurelib.load()
    reserved = {}
    for manifest in reserved_manifests or ():
        for entry in read_json(manifest)['tasks']:
            reserved.setdefault(entry['task_id'], Path(manifest).name)
    why = {t: reasons(i, audit=audit, reserved=reserved, registry=registry, min_hidden_tests=min_hidden_tests,
                      exclude_previously_used=exclude_previously_used) for t, i in pool.items()}
    eligible = {t for t, r in why.items() if not r}
    available = {d: {'pool': sum(i['difficulty'] == d for i in pool.values()),
                     'eligible': sum(pool[t]['difficulty'] == d for t in eligible),
                     'ineligible_by_reason': dict(Counter(_reason_key(r) for t, rs in why.items()
                                                          if pool[t]['difficulty'] == d for r in rs))}
                 for d in DIFFICULTIES}
    unknown = [t for t in tasks if t not in pool]
    if unknown:
        raise ValueError(f'not AtCoder stdin tasks of the pinned shard: {unknown}')
    bad = {t: why[t] for t in tasks if why[t]}
    if bad:
        raise ValueError(f'explicitly requested tasks are not eligible: {bad}')
    chosen = list(dict.fromkeys(tasks))
    removed, replacements = [], []
    if counts is None:
        if base is None and not chosen:
            raise ValueError('give counts, tasks or a base manifest')
        counts = dict(Counter(pool[t]['difficulty'] for t in chosen)) if base is None else \
            dict(Counter(e['difficulty'] for e in read_json(base)['tasks']))
    unknown_levels = set(counts) - set(DIFFICULTIES)
    if unknown_levels:
        raise ValueError(f'unknown difficulties {sorted(unknown_levels)}')
    want = {d: int(n) for d, n in counts.items() if int(n) > 0}
    have = Counter(pool[t]['difficulty'] for t in chosen)
    over = {d: have[d] for d in have if have[d] > want.get(d, 0)}
    if over:
        raise ValueError(f'explicit tasks exceed the difficulty quota: {over} vs {want}')
    pending = []   # removed base tasks still to replace: (task_id, difficulty, series)
    if base is not None:
        for entry in read_json(base)['tasks']:
            t, d = entry['task_id'], entry['difficulty']
            if t in chosen:
                continue
            if t in eligible and have[d] < want.get(d, 0):
                chosen.append(t)
                have[d] += 1
            elif t not in eligible:
                removed.append({'task_id': t, 'difficulty': d, 'n_hidden': (pool.get(t) or {}).get('n_hidden'),
                                'reasons': why.get(t, ['not an AtCoder stdin task of the pinned shard'])})
                pending.append((t, d, series(t)))
    taken = set(chosen)

    def candidates(difficulty, prefer_series=None):
        ids = [t for t in eligible if t not in taken and pool[t]['difficulty'] == difficulty
               and (prefer_series is None or pool[t]['series'] == prefer_series)]
        ordered = _order(ids, seed, difficulty)
        if prefer_unexposed:   # potentially unseen first (a public-record criterion, never an outcome)
            ordered.sort(key=lambda t: exposurelib.classify(t, registry)['class'] != 'none_known')
        return ordered

    for t, d, s in pending:
        if have[d] >= want.get(d, 0):
            continue
        same = candidates(d, s)
        pick = (same or candidates(d) or [None])[0]
        if pick is None:
            continue   # reported as a shortfall below
        chosen.append(pick)
        taken.add(pick)
        have[d] += 1
        replacements.append({'removed': t, 'replacement': pick, 'difficulty': d,
                             'stratum': f'{d}/{s}' if same else f'{d} (no eligible {s} task left)'})
    for d in DIFFICULTIES:
        need = want.get(d, 0) - have[d]
        if need > 0:
            extra = candidates(d)[:need]
            chosen += extra
            taken |= set(extra)
            have[d] += len(extra)
    short = {d: {'requested': want[d], 'selected': have[d]} for d in want if have[d] < want[d]}
    if short:
        raise InsufficientPool(
            'the eligible pool cannot fill the requested counts '
            f'{short}; available: { {d: v["eligible"] for d, v in available.items()} } '
            '(relax --min-hidden-tests, drop --exclude-previously-used, or request fewer tasks)', available)
    order = {d: i for i, d in enumerate(DIFFICULTIES)}
    chosen.sort(key=lambda t: (order[pool[t]['difficulty']], t))
    return {'selected': chosen, 'removed': removed, 'replacements': replacements, 'eligible_counts': available,
            'ineligible': {t: r for t, r in sorted(why.items()) if r}}


def task_hashes(rows, revision):
    """build_data's own conversion and hash definitions, in a scratch directory (never the study root)."""
    bd = build_data()
    with tempfile.TemporaryDirectory() as tmp:
        bd.TASKS_DIR, bd.HIDDEN_DIR = _LFPath(Path(tmp) / 'tasks'), _LFPath(Path(tmp) / 'hidden')
        bd.TASKS_DIR.mkdir()
        bd.HIDDEN_DIR.mkdir()
        out = {}
        for task_id, row in rows.items():
            entry = {'task_id': task_id, 'version': '1', 'n_hidden': None, 'public_sha256': None,
                     'hidden_sha256': None}
            bd.build(row, entry, SHARD, revision, True)
            out[task_id] = {'public_sha256': bd.sha256_dir(bd.TASKS_DIR / task_id / 'tests/public'),
                            'hidden_sha256': bd.sha256_dir(bd.HIDDEN_DIR / task_id)}
    return out


def manifest(result, pool, *, name, seed, revision, shard_sha256, config, registry=None, audit_path=AUDIT):
    """A judge manifest (same schema as judge/manifests/*.json) with selection provenance added."""
    registry = registry or exposurelib.load()
    audit = read_json(audit_path)
    hashes = task_hashes({t: pool[t]['_row'] for t in result['selected']}, revision)
    pinned = {}
    for path in sorted((REPO / 'judge/manifests').glob('*.json')):
        for entry in read_json(path)['tasks']:
            pinned[entry['task_id']] = entry
    entries = []
    for t in result['selected']:
        info = pool[t]
        if t in pinned and (pinned[t]['public_sha256'], pinned[t]['hidden_sha256']) != (
                hashes[t]['public_sha256'], hashes[t]['hidden_sha256']):
            raise RuntimeError(f'{t}: rebuilt hashes differ from the existing judge manifest')
        cls = exposurelib.classify(t, registry)
        entries.append({'task_id': t, 'version': '1', 'difficulty': info['difficulty'], 'n_public': info['n_public'],
                        'n_hidden': info['n_hidden'], **hashes[t], 'contest_date': info['contest_date'],
                        'contest_id': info['contest_id'], 'title': info['title'],
                        'output_semantics': audit['tasks'][t]['category'],
                        'exposure': cls['class'], 'exposure_sources': sorted({s['experiment'] for s in cls['sources']})})
    return {
        'name': name, 'seed': seed, 'dataset': 'livecodebench/code_generation_lite', 'hf_revision': [revision],
        'shards': [SHARD], 'counts': dict(Counter(e['difficulty'] for e in entries)),
        'selection': {
            'rule': 'outcome-blind: explicit tasks, then eligible base members, then same-stratum replacements and the '
            'remaining quota by sha256(seed:salt:difficulty:task_id); see evaluation/selection.py',
            'salt': SALT, 'config': config, 'shard_sha256': shard_sha256,
            'output_semantics_audit_sha256': sha256_file(audit_path),
            'exposure_registry_sha256': sha256_file(exposurelib.REGISTRY),
            'removed': result['removed'], 'replacements': result['replacements'],
            'eligible_counts': result['eligible_counts'],
            'exposure_counts': dict(Counter(e['exposure'] for e in entries)),
            'hidden_test_counts': dict(Counter(e['n_hidden'] for e in entries)),
        },
        'tasks': entries,
    }


def write(path, data):
    write_json(path, data)
    return path
