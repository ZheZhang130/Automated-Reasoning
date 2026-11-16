"""Validate a frozen benchmark without executing or decoding private tests."""
import argparse
import collections
import json
from pathlib import Path

from common import DATA, digest, read, save
from dataset import CACHE, EVALUATOR, EXCLUDE, REVISION


def verify(path):
    manifest = read(path)
    root = path.parent
    tasks = manifest['tasks']
    assert len(tasks) == len({t['task_id'] for t in tasks}) == 24
    assert collections.Counter(t['difficulty'] for t in tasks) == {'easy': 8, 'medium': 10, 'hard': 6}
    assert not ({t['task_id'] for t in tasks} & EXCLUDE)
    assert not ({t['task_id'] for t in tasks} & set(manifest['development_tasks']))
    assert len({t['platform'] for t in tasks}) >= 2
    assert max(collections.Counter((t['platform'], t['contest_id']) for t in tasks).values()) <= 2
    assert manifest['revision'] == REVISION and manifest['evaluator_revision'] == EVALUATOR
    assert digest(CACHE) == manifest['source_sha256']
    for info in tasks:
        public = root / 'public' / info['task_id']
        assert all(p.is_file() and not p.is_symlink() for p in public.iterdir())
        row_path = root / 'evaluator_private' / (info['task_id'] + '.json')
        row = read(row_path)
        assert digest(row_path) == info['private_row_sha256']
        assert {p.name: digest(p) for p in public.iterdir()} == info['public_sha256']
        task = read(public / 'task.json')
        assert set(task) == {'task_id', 'version', 'statement', 'submission_path'}
        assert task['statement'].startswith(row['question_content'])
        expected = json.loads(row['public_test_cases'])
        fn = json.loads(row['metadata']).get('func_name')
        if fn:
            expected = [case | {'fn_name': fn} for case in expected]
        assert read(public / 'public_tests.json') == expected
        if (public / 'solution.py').exists():
            assert (public / 'solution.py').read_text() == row['starter_code']
        assert set(p.name for p in public.iterdir()) <= {'task.json', 'public_tests.json', 'check.py', 'solution.py'}
        for key in ('question_id', 'platform', 'contest_id', 'contest_date', 'difficulty'):
            assert info[key] == row[key]
    report = {'status': 'pass', 'tasks': len(tasks), 'platforms': dict(collections.Counter(t['platform'] for t in tasks)),
              'difficulties': dict(collections.Counter(t['difficulty'] for t in tasks)),
              'source_revision': REVISION, 'manifest_sha256': digest(path),
              'distinct_contests': len({(t['platform'], t['contest_id']) for t in tasks})}
    save(root / 'verification.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    verify(parser.parse_args().manifest)
