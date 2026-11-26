"""Multi-shard task selection and preparation for enhanced_de (supports test5 + test6).

Never modifies judge/build_data.py or judge/manifests/. Builds public/hidden
suites strictly inside the separate v2 study root (e.g. E:/CSC2108Local/enhanced-de-v2-study).
"""
import hashlib
import json
from pathlib import Path

from guided_agent import output_semantics
from guided_agent.common import LCB_REVISION, REPO, read_json, sha256_file, sha256_text, utc_now, write_json
from guided_agent.tasks import CHECK_STUB, _NoTranslatePath, build_data_module, public_metadata, rows_by_id

SHARD_SHA256 = {
    'test6.jsonl': 'bb4c364f71921c4495a6ad15abe1a927350b720009f4933e2e71f8af0f6fd1f5',
    'test5.jsonl': '7f77571c2a6df0c2a72a3277650309f67e01e0008e18117e624633df53f81214',
}


def locate_shard_v2(shard_name, host_root=Path('E:/CSC2108Local'), explicit=None):
    expected = SHARD_SHA256[shard_name]
    candidates = [Path(explicit)] if explicit else []
    candidates += [
        Path(host_root) / 'cache/lcb' / shard_name,
        REPO / 'judge/.cache' / f'{LCB_REVISION[:12]}-{shard_name}',
        Path(host_root) / 'eval-v2/cache' / shard_name,
    ]
    for path in candidates:
        if path.is_file() and sha256_file(path) == expected:
            return path
    raise FileNotFoundError(f'Pinned shard {shard_name} (sha256 {expected[:12]}...) not found in {candidates}')


def select_test5_cohort(*, n_medium=8, n_hard=8, seed=2108, salt='enhanced-de-v2-test5',
                        host_root=Path('E:/CSC2108Local'), min_hidden=10):
    """Deterministically select an outcome-blind exact-output AtCoder cohort from test5.jsonl.

    Uses ONLY public metadata, public statement output-semantics classification
    (strictly requiring auto_category == 'exact' and needs_review == False so no
    ambiguous/tolerance/multi-answer/case-insensitive tasks enter), and a judge-viability
    hidden-count floor (never inspecting hidden test contents).
    """
    shard = locate_shard_v2('test5.jsonl', host_root=host_root)
    bd = build_data_module()
    rows = rows_by_id(shard)

    # Check exclusion against official final.json and exposure registry (test5 has 0 overlap, verify explicitly)
    final_ids = {t['task_id'] for t in read_json(REPO / 'judge/manifests/final.json')['tasks']}
    exposure_path = REPO / 'evaluation/data/exposure-registry.json'
    exposed_ids = set(read_json(exposure_path).get('tasks', {}).keys()) if exposure_path.exists() else set()

    eligible = {'easy': [], 'medium': [], 'hard': []}
    excluded = []
    for task_id, row in sorted(rows.items()):
        if row['platform'] != 'atcoder':
            continue
        if task_id in final_ids or task_id in exposed_ids:
            excluded.append({'task_id': task_id, 'reason': 'already_exposed'})
            continue
        public = json.loads(row['public_test_cases'])
        if not public:
            excluded.append({'task_id': task_id, 'reason': 'no_public_cases'})
            continue
        auto = output_semantics.classify(row['question_content'], [c['output'] for c in public])
        if auto['needs_review'] or auto['auto_category'] != 'exact':
            excluded.append({'task_id': task_id, 'reason': 'output_semantics_cue', 'signals': auto['signals']})
            continue
        n_hidden = len(bd.decode_private(row['private_test_cases']))
        if n_hidden < min_hidden:
            excluded.append({'task_id': task_id, 'reason': f'few_hidden:{n_hidden}'})
            continue
        diff = row['difficulty']
        if diff in eligible:
            h = hashlib.sha256(f'{seed}:{salt}:{diff}:{task_id}'.encode()).hexdigest()
            eligible[diff].append((h, public_metadata(row) | {'n_hidden': n_hidden, 'selection_hash': h}))

    for diff in eligible:
        eligible[diff].sort(key=lambda x: x[0])

    selected_medium = [item for _, item in eligible['medium'][:n_medium]]
    selected_hard = [item for _, item in eligible['hard'][:n_hard]]
    replacements_medium = [item['task_id'] for _, item in eligible['medium'][n_medium:n_medium + 4]]
    replacements_hard = [item['task_id'] for _, item in eligible['hard'][n_hard:n_hard + 4]]

    return {
        'schema': 'csc2108-enhanced-de-cohort-v1',
        'created_utc': utc_now(),
        'shard': 'test5.jsonl',
        'shard_sha256': SHARD_SHA256['test5.jsonl'],
        'hf_revision': LCB_REVISION,
        'seed': seed,
        'salt': salt,
        'rule': 'Deterministic sha256(seed:salt:difficulty:task_id) over AtCoder stdin tasks in test5.jsonl '
                'with auto_category=="exact" and needs_review==False (zero output-semantics cues), '
                f'n_hidden>={min_hidden}, zero overlap with final.json/exposure-registry.',
        'eligible_counts': {k: len(v) for k, v in eligible.items()},
        'excluded_count': len(excluded),
        'selected_counts': {'medium': len(selected_medium), 'hard': len(selected_hard)},
        'tasks': selected_medium + selected_hard,
        'replacements': {'medium': replacements_medium, 'hard': replacements_hard},
    }


def prepare_tasks_v2(task_ids, study, *, shard_name='test6.jsonl', host_root=Path('E:/CSC2108Local'), skip_existing=True):
    """Build judge/{tasks,hidden}/<id> and bundles/<id> under the separate v2 study root."""
    study = Path(study)
    shard = locate_shard_v2(shard_name, host_root=host_root)
    bd = build_data_module()
    rows = rows_by_id(shard)
    judge_root = study / 'judge'
    bd.TASKS_DIR = _NoTranslatePath(judge_root / 'tasks')
    bd.HIDDEN_DIR = _NoTranslatePath(judge_root / 'hidden')
    bd.TASKS_DIR.mkdir(parents=True, exist_ok=True)
    bd.HIDDEN_DIR.mkdir(parents=True, exist_ok=True)

    manifest_path = study / 'tasks-manifest.json'
    prior = read_json(manifest_path) if manifest_path.exists() else {'tasks': {}, 'shards': {}}
    built = {}

    for task_id in task_ids:
        bundle = study / 'bundles' / task_id
        if skip_existing and bundle.exists() and (bd.TASKS_DIR / task_id).exists() and (bd.HIDDEN_DIR / task_id).exists():
            if task_id in prior.get('tasks', {}):
                built[task_id] = prior['tasks'][task_id]
                continue
        row = rows[task_id]
        if row['platform'] != 'atcoder':
            raise ValueError(f'Only AtCoder stdin tasks supported: {task_id}')
        private = bd.decode_private(row['private_test_cases'])
        entry = {'task_id': task_id, 'version': '1', 'n_hidden': len(private),
                 'public_sha256': None, 'hidden_sha256': None}
        for directory in (bd.TASKS_DIR / task_id, bd.HIDDEN_DIR / task_id):
            if directory.exists():
                raise FileExistsError(f'{directory} exists without full manifest entry')
        bd.build(row, entry, shard_name, LCB_REVISION, True)
        public_hash = bd.sha256_dir(bd.TASKS_DIR / task_id / 'tests/public')
        hidden_hash = bd.sha256_dir(bd.HIDDEN_DIR / task_id)
        meta_path = bd.TASKS_DIR / task_id / 'task.json'
        meta = read_json(meta_path)
        meta.update(public_sha256=public_hash, hidden_sha256=hidden_hash)
        write_json(meta_path, meta)

        statement = (bd.TASKS_DIR / task_id / 'problem.md').read_text(encoding='utf-8')
        public = json.loads(row['public_test_cases'])
        bundle.mkdir(parents=True, exist_ok=False)
        write_json(bundle / 'task.json', {'task_id': task_id, 'version': '1', 'statement': statement,
                                          'submission_path': 'solution.py'})
        write_json(bundle / 'public_tests.json', [{'input': c['input'], 'output': c['output'],
                                                   'testtype': c.get('testtype', 'stdin')} for c in public])
        (bundle / 'check.py').write_text(CHECK_STUB, encoding='utf-8', newline='\n')
        built[task_id] = public_metadata(row) | {
            'shard': shard_name, 'shard_sha256': SHARD_SHA256[shard_name],
            'public_sha256': public_hash, 'hidden_sha256': hidden_hash,
            'n_hidden': len(private), 'statement_sha256': sha256_text(statement),
            'bundle_sha256': {p.name: sha256_file(p) for p in sorted(bundle.iterdir())},
        }

    prior.setdefault('shards', {})[shard_name] = SHARD_SHA256[shard_name]
    prior.setdefault('tasks', {}).update(built)
    prior['hf_revision'] = LCB_REVISION
    prior['updated_utc'] = utc_now()
    write_json(manifest_path, prior)
    return prior
