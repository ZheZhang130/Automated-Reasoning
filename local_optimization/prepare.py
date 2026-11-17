"""Freeze fresh, contest-separated metadata-selected splits without solving tasks."""
import collections
import hashlib
import json
import shutil

from optlib import DATA, ROOT, V2, digest, read, save
from dataset import CACHE, EVALUATOR, REVISION


def prepare():
    target = DATA / 'dataset'
    if target.exists():
        raise ValueError('Never replace an existing frozen dataset')
    excluded = {'atcoder-abc301_a', 'atcoder-abc301_c', 'atcoder-abc301_e'}
    prior = read(V2 / 'evaluation_manifest.json')
    excluded.update(t['task_id'] for t in prior['tasks'])
    discovery = []
    for path in DATA.parent.rglob('private_evaluation.json'):
        try:
            result = path.parent / 'result.json'
            task = read(result) if result.exists() else read(path.parent / 'task.json')
            key = task.get('task_id') or task.get('task', {}).get('task_id')
            if key and not key.startswith(('dev-', 'fixture-')):
                excluded.add(key)
                discovery.append({'path': str(path), 'task_id': key, 'sha256': digest(path)})
        except (ValueError, OSError):
            continue
    pool, counts = [], collections.Counter()
    for number, line in enumerate(CACHE.open(encoding='utf-8')):
        row = json.loads(line)
        key = row['platform'] + '-' + row['question_id']
        public = json.loads(row['public_test_cases'])
        fn = json.loads(row['metadata']).get('func_name')
        supported = (public and all(t['testtype'] == 'stdin' for t in public) and not fn) or (
            isinstance(fn, str) and fn.isidentifier() and 'class Solution' in row['starter_code']
            and not any(n in row['starter_code'] for n in ('TreeNode', 'ListNode', 'Node[')))
        if key not in excluded and supported and public and '<img' not in row['question_content'] and '![' not in row['question_content']:
            pool.append({k: row[k] for k in ('platform', 'difficulty', 'question_id', 'contest_id', 'contest_date')} |
                        {'task_id': key, 'line_number': number, 'submission_type': 'functional' if fn else 'stdin_stdout'})
            counts[(row['platform'], row['difficulty'])] += 1
    seen_contests = set()
    prior_contests = {(t['platform'], t['contest_id']) for t in prior['tasks']}
    splits = {}
    # Held-out first prevents development choices from constraining its balance.
    for split, targets in [('heldout', [6, 8, 6]), ('selection', [4, 4, 4]), ('development', [2, 2, 2])]:
        chosen, contest_counts = [], collections.Counter()
        for difficulty, count in zip(['easy', 'medium', 'hard'], targets):
            platform_counts = collections.Counter()
            for _ in range(count):
                eligible = [t for t in pool if t['difficulty'] == difficulty
                            and (t['platform'], t['contest_id']) not in seen_contests
                            and (split != 'heldout' or (t['platform'], t['contest_id']) not in prior_contests)
                            and contest_counts[(t['platform'], t['contest_id'])] < 2]
                if not eligible:
                    raise ValueError('Insufficient contest-disjoint tasks: ' + split + '/' + difficulty)
                platforms = sorted({t['platform'] for t in eligible}, key=lambda p: (platform_counts[p], p))
                eligible = [t for t in eligible if t['platform'] == platforms[0]]
                selected = min(eligible, key=lambda t: hashlib.sha256(('CSC2108-opt-20261117:' + split + ':' + t['task_id']).encode()).hexdigest())
                chosen.append(selected)
                pool.remove(selected)
                platform_counts[selected['platform']] += 1
                contest_counts[(selected['platform'], selected['contest_id'])] += 1
        seen_contests.update(contest_counts)
        splits[split] = chosen
    wanted = {t['line_number']: (split, t) for split, tasks in splits.items() for t in tasks}
    for number, line in enumerate(CACHE.open(encoding='utf-8')):
        if number not in wanted:
            continue
        split, info = wanted[number]
        row = json.loads(line)
        fn = json.loads(row['metadata']).get('func_name')
        folder = target / split / 'public' / info['task_id']
        folder.mkdir(parents=True)
        save(folder / 'task.json', {'task_id': info['task_id'], 'version': REVISION,
            'statement': row['question_content'] + ('\n\nImplement the provided Solution class method ' + fn if fn else '\n\nWrite a standalone Python stdin/stdout program') + ' at /workspace/solution.py. Public example tests: python -I /public/check.py',
            'submission_path': 'solution.py'})
        tests = json.loads(row['public_test_cases'])
        save(folder / 'public_tests.json', [t | {'fn_name': fn} for t in tests] if fn else tests)
        shutil.copyfile(V2 / 'public_check.py', folder / 'check.py')
        if row.get('starter_code', '').strip():
            (folder / 'solution.py').write_text(row['starter_code'], encoding='utf-8')
        private = target / split / 'evaluator_private' / (info['task_id'] + '.json')
        save(private, row)
        info.update(private_row_sha256=digest(private), public_sha256={p.name: digest(p) for p in folder.iterdir()})
    common = {'dataset': prior['dataset'], 'revision': REVISION, 'source_sha256': digest(CACHE),
              'evaluator_revision': EVALUATOR, 'excluded_previously_scored': sorted(excluded),
              'selection': 'PLAN.md; heldout first, SHA256 salted order, platform round robin, contest-disjoint splits, max 2/contest; heldout excludes prior eval contests',
              'eligible_counts': {str(k): v for k, v in counts.items()}}
    for split, tasks in splits.items():
        manifest = common | {'split': split, 'tasks': tasks}
        save(target / split / 'manifest.json', manifest)
        save(ROOT / (split + '_manifest.json'), manifest)
    save(DATA / 'exclusion-audit.json', {'excluded': sorted(excluded), 'discovered_scored_artifacts': discovery})
    print(json.dumps({'splits': {k: len(v) for k, v in splits.items()}, 'excluded': len(excluded), 'source_sha256': common['source_sha256']}))


if __name__ == '__main__':
    prepare()
