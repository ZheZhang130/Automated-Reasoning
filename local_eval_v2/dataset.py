"""Freeze a varied Python manifest from the newest compatible official dataset slice."""
import argparse
import collections
import json
import shutil
from urllib.request import urlopen

from common import DATA, ROOT, digest, read, save

REVISION = '0fe84c3912ea0c4d4a78037083943e8f0c4dd505'
EVALUATOR = '28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24'
FILENAME = 'test6.jsonl'
CACHE = DATA / 'cache' / FILENAME
EXCLUDE = {'atcoder-abc301_a', 'atcoder-abc301_c', 'atcoder-abc301_e'}


def download():
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    if not CACHE.exists():
        partial = CACHE.with_suffix('.partial')
        url = f'https://huggingface.co/datasets/livecodebench/code_generation_lite/resolve/{REVISION}/{FILENAME}'
        with urlopen(url, timeout=180) as response, partial.open('wb') as target:
            shutil.copyfileobj(response, target, length=8 * 1024 * 1024)
        partial.rename(CACHE)
    print(json.dumps({'file': str(CACHE), 'bytes': CACHE.stat().st_size, 'sha256': digest(CACHE)}), flush=True)


def select():
    root = DATA / 'evaluation-24'
    root.mkdir(exist_ok=False)
    candidates = []
    counts = collections.Counter()
    with CACHE.open(encoding='utf-8') as stream:
        for number, line in enumerate(stream):
            row = json.loads(line)
            key = row['platform'] + '-' + row['question_id']
            public = json.loads(row['public_test_cases'])
            fn = json.loads(row['metadata']).get('func_name')
            supported = (all(t['testtype'] == 'stdin' for t in public) and not fn) or (
                isinstance(fn, str) and fn.isidentifier() and 'class Solution' in row['starter_code']
                and not any(name in row['starter_code'] for name in ('TreeNode', 'ListNode', 'Node[')))
            valid = (key not in EXCLUDE and public and supported
                     and '<img' not in row['question_content'] and '![' not in row['question_content'])
            counts[(row['platform'], row['difficulty'], bool(valid))] += 1
            if valid:
                candidates.append({k: row[k] for k in ('platform', 'difficulty', 'question_id', 'contest_id', 'contest_date')} |
                                  {'task_id': key, 'line_number': number})
    selected = []
    contests = collections.Counter()
    for difficulty, target in [('easy', 8), ('medium', 10), ('hard', 6)]:
        platform_counts = collections.Counter()
        pool = [c for c in candidates if c['difficulty'] == difficulty]
        pool.sort(key=lambda c: (c['contest_date'], c['task_id']), reverse=True)
        for _ in range(target):
            eligible = [c for c in pool if contests[(c['platform'], c['contest_id'])] < 2]
            if not eligible:
                raise ValueError('Insufficient compatible distinct tasks for difficulty ' + difficulty)
            platforms = sorted({c['platform'] for c in eligible}, key=lambda p: (platform_counts[p], p))
            chosen = next(c for c in eligible if c['platform'] == platforms[0])
            selected.append(chosen)
            pool.remove(chosen)
            platform_counts[chosen['platform']] += 1
            contests[(chosen['platform'], chosen['contest_id'])] += 1
    wanted = {r['line_number']: r for r in selected}
    with CACHE.open(encoding='utf-8') as stream:
        for number, line in enumerate(stream):
            if number not in wanted:
                continue
            info = wanted[number]
            row = json.loads(line)
            fn = json.loads(row['metadata']).get('func_name')
            info['submission_type'] = 'functional' if fn else 'stdin_stdout'
            info['function_name'] = fn
            folder = root / 'public' / info['task_id']
            folder.mkdir(parents=True)
            task = {'task_id': info['task_id'], 'version': REVISION,
                    'statement': row['question_content'] + ('\n\nImplement the provided Solution class method ' + fn if fn else '\n\nWrite a standalone Python stdin/stdout program') + ' at /workspace/solution.py. Public example tests: python -I /public/check.py',
                    'submission_path': 'solution.py'}
            save(folder / 'task.json', task)
            public = json.loads(row['public_test_cases'])
            if fn:
                public = [t | {'fn_name': fn} for t in public]
            save(folder / 'public_tests.json', public)
            shutil.copyfile(ROOT / 'public_check.py', folder / 'check.py')
            if row.get('starter_code', '').strip():
                (folder / 'solution.py').write_text(row['starter_code'], encoding='utf-8')
            private_path = root / 'evaluator_private' / (info['task_id'] + '.json')
            save(private_path, row)
            info['private_row_sha256'] = digest(private_path)
            info['public_sha256'] = {p.name: digest(p) for p in folder.iterdir()}
    manifest = {'dataset': 'livecodebench/code_generation_lite', 'revision': REVISION,
                'release': 'release_v6', 'slice': 'v6 (test6.jsonl; newest component only)',
                'source_file': FILENAME, 'source_sha256': digest(CACHE), 'evaluator_revision': EVALUATOR,
                'selection_rule': '8 easy/10 medium/6 hard; latest compatible slice; round-robin platforms within difficulty, newest date first; max two tasks per platform/contest; stdin or JSON functional interfaces; exclude custom node types and image statements',
                'excluded': sorted(EXCLUDE), 'development_tasks': ['dev-negative-squares', 'dev-balanced-delimiters', 'dev-ascii-case', 'dev-functional-distinct'],
                'eligible_counts': {str(k): v for k, v in counts.items()}, 'tasks': selected}
    save(root / 'manifest.json', manifest)
    save(ROOT / 'evaluation_manifest.json', manifest)
    print(json.dumps({'manifest': str(root / 'manifest.json'), 'tasks': selected}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['download', 'select'])
    args = parser.parse_args()
    download() if args.action == 'download' else select()
