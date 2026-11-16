"""Small synthetic development set; disjoint from all LiveCodeBench tasks."""
import shutil
import argparse
import json
from pathlib import Path
from common import DATA, ROOT, digest, save


def main():
    definitions = [
        ('dev-negative-squares', 'Repair solution.py. Read n followed by n signed integers. Print the sum of the squares of the strictly negative integers. Zero and positive integers contribute nothing. n may be zero.',
         'import sys\nn, *values = map(int, sys.stdin.read().split())\nprint(sum(v*v for v in values))\n',
         [('5\n-3 2 -1 0 4\n', '10\n'), ('3\n1 2 3\n', '0\n')],
         [('4\n-5 -5 2 -1\n', '51\n'), ('0\n', '0\n'), ('1\n-7\n', '49\n')]),
        ('dev-balanced-delimiters', 'Read one line consisting of parentheses (), square brackets [], and braces {}. Print YES if all delimiters are properly nested and matched, otherwise NO. An empty line is valid.', '',
         [('([]){}\n', 'YES\n'), ('([)]\n', 'NO\n'), ('\n', 'YES\n')],
         [('{[()]}\n', 'YES\n'), ('(]\n', 'NO\n'), ('(\n', 'NO\n'), ('}\n', 'NO\n')]),
        ('dev-ascii-case', 'Read the input text. Change every ASCII uppercase letter to lowercase and every ASCII lowercase letter to uppercase, preserving all other characters and line breaks. Write the transformed text.', '',
         [('Hello, CSC2108!\n', 'hELLO, csc2108!\n'), ("Back\\slash 'q'\nNEXT\n", "bACK\\SLASH 'Q'\nnext\n")],
         [('AZaz09 []\n', 'azAZ09 []\n'), ('', ''), ('a\nb\nC\n', 'A\nB\nc\n')])
    ]
    definitions.append(('dev-functional-distinct', 'Implement Solution.countDistinct(values), returning the number of distinct integers in values. The list may be empty. Use the supplied class and method interface.',
                        'class Solution:\n    def countDistinct(self, values: list[int]) -> int:\n        return 0\n',
                        [('1 1 2', '2'), ('', '0')], [('4 4 4', '1'), ('0 -1 0 2', '3')]))
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=DATA / 'development-v5')
    args = parser.parse_args()
    root = args.output
    root.mkdir(exist_ok=False)
    tasks = []
    for name, statement, starter, public, heldout in definitions:
        folder = root / 'public' / name
        folder.mkdir(parents=True)
        save(folder / 'task.json', {'task_id': name, 'version': 'synthetic-dev-1', 'statement': statement, 'submission_path': 'solution.py'})
        functional = name == 'dev-functional-distinct'
        cases = lambda pairs: ([{'input': json.dumps([int(x) for x in i.split()]), 'output': o,
                                 'testtype': 'functional', 'fn_name': 'countDistinct'} for i, o in pairs] if functional else
                               [{'input': i, 'output': o, 'testtype': 'stdin'} for i, o in pairs])
        save(folder / 'public_tests.json', cases(public))
        shutil.copyfile(ROOT / 'public_check.py', folder / 'check.py')
        if starter:
            (folder / 'solution.py').write_text(starter, encoding='utf-8')
        save(root / 'private' / (name + '.json'), {'public_test_cases': __import__('json').dumps(cases(public)),
             'private_test_cases': __import__('json').dumps(cases(heldout)), 'metadata': json.dumps({'func_name': 'countDistinct'} if functional else {})})
        tasks.append({'task_id': name, 'public_sha256': {p.name: digest(p) for p in folder.iterdir()}})
    save(root / 'manifest.json', {'kind': 'development_only', 'tasks': tasks})
    print(root)


if __name__ == '__main__':
    main()
