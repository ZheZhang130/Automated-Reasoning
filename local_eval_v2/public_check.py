"""Only public stdin/stdout examples; this file is the only test adapter agents see."""
import json
import subprocess
import sys
from pathlib import Path

cases = json.loads(Path('/public/public_tests.json').read_text())
PREFIX = '''from string import *
from re import *
from datetime import *
from collections import *
from heapq import *
from bisect import *
from copy import *
from math import *
from random import *
from statistics import *
from itertools import *
from functools import *
from operator import *
from io import *
from sys import *
from json import *
from builtins import *
from typing import *
import string, re, datetime, collections, heapq, bisect, copy, math, random, statistics, itertools, functools, operator, io, sys, json
sys.setrecursionlimit(50000)
'''
if len(sys.argv) == 3 and sys.argv[1] == '--functional-index':
    case = cases[int(sys.argv[2])]
    namespace = {'__name__': 'candidate'}
    exec(compile(PREFIX + '\n' + Path('/workspace/solution.py').read_text(), '/workspace/solution.py', 'exec'), namespace)
    target = namespace['Solution']() if 'Solution' in namespace else namespace
    method = getattr(target, case['fn_name']) if not isinstance(target, dict) else target[case['fn_name']]
    prediction = method(*[json.loads(line) for line in case['input'].split('\n')])
    if isinstance(prediction, tuple):
        prediction = list(prediction)
    print('CSC2108_FUNCTION_VALUE=' + json.dumps(prediction))
    raise SystemExit(0)
for index, case in enumerate(cases, 1):
    try:
        functional = bool(case.get('fn_name'))
        command = ['python', '-I', '/public/check.py', '--functional-index', str(index-1)] if functional else ['python', '-I', '/workspace/solution.py']
        result = subprocess.run(command, input=case['input'],
                                text=True, capture_output=True, timeout=6)
        if functional and result.returncode == 0:
            values = [line.split('=', 1)[1] for line in result.stdout.splitlines() if line.startswith('CSC2108_FUNCTION_VALUE=')]
            ok = bool(values) and json.loads(values[-1]) == json.loads(case['output'])
        else:
            ok = result.returncode == 0 and result.stdout.split() == case['output'].split()
        feedback = {'case': index, 'status': 'pass' if ok else 'candidate_failure',
                    'returncode': result.returncode, 'input': case['input'][:1000],
                    'expected': case['output'][:1000], 'actual': result.stdout[:1000],
                    'stderr': result.stderr[-1200:]}
    except subprocess.TimeoutExpired:
        ok = False
        feedback = {'case': index, 'status': 'candidate_timeout'}
    if not ok:
        print('CSC2108_PUBLIC_RESULT=' + json.dumps(feedback))
        raise SystemExit(1)
print('CSC2108_PUBLIC_RESULT=' + json.dumps({'status': 'pass', 'cases': len(cases)}))
