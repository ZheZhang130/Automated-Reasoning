"""Statement-only D2 contracts, isolated verification banks and advisory gates."""

import ast
import base64
import json
import math
import re
import subprocess
import time
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path

from guided_agent.checkers import outputs_match
from guided_agent.common import REPO, sha256_bytes, sha256_text, utc_now, write_json

from . import ledger_guard


D2_BUNDLE_V1 = """Write a verification bundle from the supplied problem statement alone.
Use no tools, hidden tests, candidate code, solution algorithm, data structure,
or implementation plan. Return exactly these two sections:

## Contract
Write a concise, semi-formal behavioral contract. Use POST-1, POST-2, ... to
identify observable requirements, edge/corner cases, bounds, and complexity
requirements stated or implied by the limits. Do not give an algorithm or hints.

## Verification Module
Return exactly one fenced ```python code block. Define pure functions, with no
file I/O, network, subprocesses, reflection, or third-party imports. Use only
pure standard-library operations (e.g. math, itertools, collections, random,
functools, re, bisect, heapq, decimal, fractions, string, copy). Use seeded
random.Random instances if needed. At module level use only imports, literal
constants, and undecorated function definitions. Small helpers are allowed.

Define all six functions:
- validate_input(inp: str) -> bool: True iff all input preconditions hold.
- gen_small(seed: int, n: int) -> list[str]: n deterministic valid inputs,
  including boundaries and corner cases, with N tiny (typically <= 6–8).
- gen_stress(seed: int) -> list[str]: two deterministic valid adversarial inputs
  near the bounds, or at a scale a fast solution handles within two seconds.
  Exercise quadratic time or recursion-depth failures where applicable.
- check_postconditions(inp: str, out: str) -> list[tuple[str, str]]: check output
  syntax, bounds, and structural invariants without re-solving the problem.
  Return [] or (POST ID, reason) pairs using the contract IDs.
- metamorphic_pairs(seed: int, n: int) -> list[tuple[str, str, str, str]]: up to
  n (POST ID, relation, input1, input2) tuples. Relations are equal (judge output
  equality), le/ge (one finite numeric token per output, in input order), or
  same_yes_no (one Yes/No token per output, case insensitive). Return [] if no
  sound relation applies. Never invent one.
- reference_small(inp: str) -> str | None: literal, exhaustive specification
  evaluator for tiny inputs. Return None if too large for fast exact evaluation
  or if a unique expected output cannot be given. Never approximate.
"""

_FUNCTIONS = frozenset({
    'validate_input', 'gen_small', 'gen_stress', 'check_postconditions',
    'metamorphic_pairs', 'reference_small',
})
_MODES = ('inputs-stress', 'property', 'oracle')
_RELATIONS = frozenset({'equal', 'le', 'ge', 'same_yes_no'})
_FAILURES = ('RE', 'TLE', 'postcondition', 'metamorphic', 'oracle_mismatch')
_COUNT_KEYS = ('small_ran', 'stress_ran', 'meta_ran', 're', 'tle', 'post_fail', 'meta_fail', 'oracle_mismatch')
_IMAGE = 'python:3.11-slim-bookworm'
_SMALL_LIMIT = 4_000
_STRESS_LIMIT = 8_000_000
_POST_ID = re.compile(r'POST-[1-9][0-9]*')

_SAFE_IMPORTS = {
    'math': ('acos asin atan atan2 ceil comb cos degrees dist e exp fabs factorial floor fmod '
             'frexp fsum gcd hypot inf isclose isfinite isinf isnan isqrt lcm ldexp log log10 log2 '
             'modf nan perm pi pow prod radians remainder sin sqrt tan tau trunc'),
    'itertools': ('accumulate chain combinations combinations_with_replacement compress count '
                  'cycle dropwhile filterfalse groupby islice pairwise permutations product repeat '
                  'starmap takewhile tee zip_longest'),
    'collections': 'ChainMap Counter OrderedDict defaultdict deque',
    'random': 'Random',
    'functools': 'cache cmp_to_key lru_cache partial reduce',
    're': ('A ASCII DOTALL I IGNORECASE M MULTILINE S VERBOSE X compile escape findall finditer '
           'fullmatch match search split sub subn'),
    'bisect': 'bisect bisect_left bisect_right insort insort_left insort_right',
    'heapq': 'heapify heappop heappush heappushpop heapreplace merge nlargest nsmallest',
    'decimal': ('Context Decimal DecimalException DivisionByZero InvalidOperation ROUND_CEILING '
                'ROUND_DOWN ROUND_FLOOR ROUND_HALF_DOWN ROUND_HALF_EVEN ROUND_HALF_UP ROUND_UP '
                'getcontext localcontext'),
    'fractions': 'Fraction',
    'string': 'ascii_letters ascii_lowercase ascii_uppercase digits hexdigits octdigits punctuation whitespace',
    'copy': 'copy deepcopy',
}
_SAFE_BUILTINS = (
    'abs all any bool bytes chr dict divmod enumerate filter float format frozenset int isinstance '
    'issubclass iter len list map max min next ord pow range repr reversed round set slice sorted '
    'str sum tuple zip ArithmeticError AssertionError Exception IndexError KeyError LookupError '
    'OverflowError RuntimeError StopIteration TypeError ValueError ZeroDivisionError'
)
_BLOCKED_NAMES = frozenset({
    'os', 'sys', 'subprocess', 'socket', 'urllib', 'http', 'shutil', 'pathlib',
    'ctypes', 'importlib', 'builtins', 'open', 'exec', 'eval', 'compile', 'getattr',
    'setattr', 'delattr', 'globals', 'locals', 'vars', 'dir', 'type', 'input',
    'breakpoint', 'help', 'print', 'format_map',
})
_SAFE_AST = (
    ast.Module, ast.Import, ast.ImportFrom, ast.alias, ast.FunctionDef, ast.arguments, ast.arg,
    ast.Return, ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Delete, ast.For, ast.While, ast.If,
    ast.With, ast.withitem, ast.Raise, ast.Try, ast.ExceptHandler, ast.Assert, ast.Expr,
    ast.Pass, ast.Break, ast.Continue, ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.IfExp,
    ast.Dict, ast.Set, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp, ast.comprehension,
    ast.Yield, ast.YieldFrom, ast.Compare, ast.Call, ast.keyword, ast.FormattedValue, ast.JoinedStr,
    ast.Constant, ast.Attribute, ast.Subscript, ast.Starred, ast.Name, ast.List, ast.Tuple, ast.Slice,
    ast.Lambda, ast.Nonlocal, ast.expr_context, ast.boolop, ast.operator, ast.unaryop, ast.cmpop,
)


def _is_safe_cache_decorator(node):
    """Allow only functools.cache / functools.lru_cache memoization decorators."""
    target = node.func if isinstance(node, ast.Call) else node
    if isinstance(target, ast.Name):
        return target.id in ('cache', 'lru_cache')
    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
        return target.value.id == 'functools' and target.attr in ('cache', 'lru_cache')
    return False


class D2SandboxError(RuntimeError):
    """The isolated dispatcher could not produce an evaluation result."""


def _check_identifier(name):
    if name and (name.startswith('__') or name in _BLOCKED_NAMES):
        raise ValueError(f'Unsafe name in verification module: {name}')


def _eval_constant_expr(node, constants):
    """Evaluate pure literal/arithmetic module constants without calls or huge shifts."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, str, bytes, bool, type(None))):
            return node.value
        raise ValueError(f'Unsupported module constant type: {type(node.value).__name__}')
    if isinstance(node, ast.Name):
        if node.id in constants:
            return constants[node.id]
        raise ValueError(f'Undefined module constant reference: {node.id}')
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        vals = [_eval_constant_expr(elt, constants) for elt in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(vals)
        if isinstance(node, ast.Set):
            return set(vals)
        return vals
    if isinstance(node, ast.Dict):
        if any(k is None for k in node.keys):
            raise ValueError('Dict unpacking is unsupported in module constants')
        return {_eval_constant_expr(k, constants): _eval_constant_expr(v, constants)
                for k, v in zip(node.keys, node.values)}
    if isinstance(node, ast.UnaryOp):
        val = _eval_constant_expr(node.operand, constants)
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            raise ValueError('Unary constant operator requires numeric operand')
        if isinstance(node.op, ast.UAdd):
            return +val
        if isinstance(node.op, ast.USub):
            return -val
        if isinstance(node.op, ast.Invert) and isinstance(val, int):
            return ~val
        raise ValueError(f'Unsupported unary constant operator: {type(node.op).__name__}')
    if isinstance(node, ast.BinOp):
        left = _eval_constant_expr(node.left, constants)
        right = _eval_constant_expr(node.right, constants)
        if isinstance(left, bool) or isinstance(right, bool) or not (
            isinstance(left, (int, float)) and isinstance(right, (int, float))
        ):
            raise ValueError('Binary constant operator requires numeric operands')
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.FloorDiv):
            return left // right
        if isinstance(node.op, ast.Mod):
            return left % right
        if isinstance(node.op, ast.Pow):
            if not isinstance(right, (int, float)) or abs(right) > 100:
                raise ValueError('Constant exponent exceeds bound (|exp| <= 100)')
            return left ** right
        if isinstance(node.op, ast.LShift) and isinstance(left, int) and isinstance(right, int):
            if right < 0 or right > 256:
                raise ValueError('Constant shift exceeds bound (0 <= shift <= 256)')
            return left << right
        if isinstance(node.op, ast.RShift) and isinstance(left, int) and isinstance(right, int):
            if right < 0 or right > 256:
                raise ValueError('Constant shift exceeds bound (0 <= shift <= 256)')
            return left >> right
        raise ValueError(f'Unsupported binary constant operator: {type(node.op).__name__}')
    raise ValueError(f'Module constants must be pure literal or numeric expressions, got {type(node).__name__}')


def _check_module(code):
    """Validate module syntax and restrict imports, initialization and introspection."""
    tree = ast.parse(code)
    definitions = []
    constants = {}
    for index, node in enumerate(tree.body):
        if isinstance(node, ast.FunctionDef):
            definitions.append(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if any((alias.asname or alias.name) in _FUNCTIONS for alias in node.names):
                raise ValueError('Imports cannot replace required functions')
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(not isinstance(target, ast.Name) or target.id in _FUNCTIONS for target in targets):
                raise ValueError('Module constants must have simple names')
            if node.value is None:
                raise ValueError('Module constant annotation requires a value')
            val = _eval_constant_expr(node.value, constants)
            for target in targets:
                constants[target.id] = val
        elif not (index == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                  and isinstance(node.value.value, str)):
            raise ValueError('Module scope permits only imports, literal constants and functions')

    missing = sorted(_FUNCTIONS.difference(definitions))
    if missing or len(set(definitions)) != len(definitions):
        raise ValueError(f'Missing or duplicate verification functions (missing: {missing})')

    for node in ast.walk(tree):
        if not isinstance(node, _SAFE_AST):
            raise ValueError(f'Unsafe verification syntax: {type(node).__name__}')
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in _SAFE_IMPORTS:
                    raise ValueError(f'Unsafe import: {alias.name}')
        if isinstance(node, ast.ImportFrom):
            allowed = _SAFE_IMPORTS.get(node.module, '').split()
            if node.level or any(alias.name not in allowed for alias in node.names):
                raise ValueError(f'Unsafe import from {node.module}')
        if isinstance(node, ast.Attribute):
            if node.attr.startswith('_') or node.attr == 'format':
                raise ValueError(f'Unsafe attribute: {node.attr}')
            # re.compile is a permitted regex operation, unlike the builtin compile.
            if node.attr != 'compile':
                _check_identifier(node.attr)
        if isinstance(node, ast.FunctionDef) and node.decorator_list:
            if node.name in _FUNCTIONS or not all(_is_safe_cache_decorator(dec) for dec in node.decorator_list):
                raise ValueError('Verification function decorators are unsupported')
        for node_type, field in ((ast.Name, 'id'), (ast.FunctionDef, 'name'), (ast.arg, 'arg'),
                                 (ast.alias, 'asname'), (ast.ExceptHandler, 'name')):
            if isinstance(node, node_type):
                _check_identifier(getattr(node, field))
    # ast.parse alone accepts constructs such as a loop control statement outside a loop.
    compile(tree, '<d2-module>', 'exec')


def parse_bundle_response(text):
    """Return ``(contract_md, module_code)`` from the two required sections."""
    match = re.fullmatch(
        r'\s*## Contract[ \t]*\n(?P<contract>.+?)\n## Verification Module[ \t]*\n'
        r'\s*```python[ \t]*\n(?P<code>.+?)\n```[ \t]*\s*',
        text.replace('\r\n', '\n'), re.DOTALL,
    )
    if not match:
        raise ValueError('Expected a Contract section followed by one fenced Python verification module')
    contract, code = (match[name].strip() for name in ('contract', 'code'))
    if (not _POST_ID.search(contract) or re.search(r'^\s*```', contract, re.MULTILINE)
            or re.search(r'^\s*##\s', contract, re.MULTILINE)):
        raise ValueError('Expected one contract with POST IDs and one code fence')
    _check_module(code)
    return contract, code


def author_d2_bundle(*, statement, task_id, out_path, provider='codex', work_root=None,
                     ledger_path=None, fixed_response=None, model='gpt-6.2-sol', effort='medium',
                     timeout=300, max_completion_tokens=8000):
    """Author once at ``out_path`` and bind the artifact to the statement and prompt."""
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(path.name + '.lock')
    # Hold the reservation across the provider call, including when another authoring run starts.
    with lock.open('x', encoding='utf-8'):
        pass
    try:
        if path.exists():
            raise FileExistsError(f'D2 artifact already exists: {path}')
        if provider == 'fixed':
            if not isinstance(fixed_response, str):
                raise ValueError('The fixed provider requires fixed_response text')
            result = {'text': fixed_response}
        elif provider == 'codex':
            result = ledger_guard.isolated_codex_infer(
                system=D2_BUNDLE_V1, user=statement, evidence=path.with_name(path.name + '.codex'),
                work_root=work_root or path.parent / 'd2-isolation', model=model, effort=effort,
                timeout=timeout,
            )
        elif provider == 'api':
            if ledger_path is None:
                raise ValueError('The API provider requires an explicit v2 ledger_path')
            result = ledger_guard.guarded_api_chat(
                messages=[{'role': 'system', 'content': D2_BUNDLE_V1},
                          {'role': 'user', 'content': statement}],
                ledger_path=ledger_path, entry={'task_id': task_id, 'kind': 'd2-contract',
                                                'prompt_id': 'D2_BUNDLE_V1'},
                max_completion_tokens=max_completion_tokens, effort=effort, timeout=timeout,
            )
            if result['finish_reason'] != 'stop':
                raise RuntimeError(f"D2 authoring stopped with finish_reason={result['finish_reason']}")
        else:
            raise ValueError(f'Unknown D2 provider: {provider}')

        contract, code = parse_bundle_response(result['text'])
        artifact = {
            'schema': 'csc2108-d2-bundle-v1', 'task_id': task_id, 'provider': provider,
            'prompt_id': 'D2_BUNDLE_V1', 'statement_sha256': sha256_text(statement),
            'prompt_sha256': sha256_text(D2_BUNDLE_V1), 'contract_md': contract, 'module_code': code,
            'response_sha256': sha256_text(result['text']), 'created_utc': utc_now(),
        }
        artifact.update({k: result[k] for k in ('isolation', 'usage', 'wall_seconds', 'api_model',
                         'ledger_index', 'request_id', 'latency_seconds', 'cost_usd') if k in result})
        write_json(path, artifact)
        return artifact
    finally:
        lock.unlink()


def run_in_throwaway_docker(script_code, stdin_payload, *, timeout=25.0, memory='512m'):
    """Run a trusted JSON dispatcher in a fresh container with no host mounts."""
    name = 'csc2108-d2-' + uuid.uuid4().hex
    command = [
        'docker', 'run', '--rm', '-i', '--name', name, '--pull', 'never', '--network', 'none',
        '--read-only', '--user', '65534:65534', '--memory', memory, '--pids-limit', '64',
        '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
        '--tmpfs', '/tmp:rw,noexec,nosuid,size=64m', _IMAGE, 'python', '-I', '-c', script_code,
    ]
    payload = json.dumps(stdin_payload).encode('utf-8')
    try:
        result = subprocess.run(command, input=payload, capture_output=True, timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        # Killing the local Docker client does not guarantee that Docker removed its container.
        try:
            subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            pass
        raise
    except OSError as exc:
        raise D2SandboxError(f'Could not start the D2 Docker dispatcher: {exc}') from exc
    if result.returncode:
        detail = result.stderr[-2000:].decode('utf-8', 'replace').strip()
        raise D2SandboxError(f'D2 Docker dispatcher failed ({result.returncode}): {detail}')
    try:
        return json.loads(result.stdout)
    except (UnicodeError, ValueError) as exc:
        raise D2SandboxError('D2 Docker dispatcher returned invalid JSON') from exc


# Both dispatchers are trusted code. Payloads carry untrusted code only over stdin.
_CONTAINER_SUPPORT = r'''
import json
import os
import resource
import signal
import subprocess
import sys
import tempfile


def cap_file_output():
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 << 20, 16 << 20))


def capture(argv, data, timeout, cwd=None):
    with tempfile.TemporaryFile(dir='/tmp') as stdout, tempfile.TemporaryFile(dir='/tmp') as stderr:
        with subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                              cwd=cwd, start_new_session=True, preexec_fn=cap_file_output) as proc:
            timed_out = False
            try:
                proc.communicate(data, timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
            finally:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait()
            if timed_out:
                return 'timeout', b'', b''
        stdout.seek(0)
        stderr.seek(0, 2)
        stderr.seek(max(0, stderr.tell() - 2000))
        return ('ok' if proc.returncode == 0 else 'error'), stdout.read(), stderr.read()
'''

_MODULE_WORKER = (
    f'SAFE_IMPORTS = {_SAFE_IMPORTS!r}\nSAFE_BUILTINS = {_SAFE_BUILTINS!r}\n' + r'''
import __future__
import builtins
import importlib
import json
import sys
from types import SimpleNamespace


def pure_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level or name not in SAFE_IMPORTS:
        raise ImportError(name)
    module = importlib.import_module(name)
    return SimpleNamespace(**{key: getattr(module, key) for key in SAFE_IMPORTS[name].split()})


request = json.load(sys.stdin)
allowed = {name: getattr(builtins, name) for name in SAFE_BUILTINS.split()}
allowed['__import__'] = pure_import
namespace = {'__builtins__': allowed, '__name__': 'd2_verification'}
try:
    exec(compile(request['code'], '<d2-module>', 'exec', flags=__future__.annotations.compiler_flag), namespace)
    value = namespace[request['function']](*request['args'])
    response = json.dumps({'status': 'ok', 'value': value}, allow_nan=False)
except BaseException as error:
    response = json.dumps({'status': 'error', 'error': type(error).__name__})
sys.stdout.write(response)
''')

_MODULE_DISPATCHER = (
    _CONTAINER_SUPPORT + f'\nWORKER = {_MODULE_WORKER!r}\n'
    + f'SMALL_LIMIT = {_SMALL_LIMIT}\nSTRESS_LIMIT = {_STRESS_LIMIT}\nRELATIONS = {sorted(_RELATIONS)!r}\n'
    + f'POST_ID = {_POST_ID.pattern!r}\n' + r'''
import re


def invoke(function, *args):
    payload = json.dumps({'code': req['module_code'], 'function': function, 'args': args}).encode()
    status, out, _ = capture([sys.executable, '-I', '-c', WORKER], payload, req['per_case_timeout'])
    if status != 'ok':
        return {'status': status}
    try:
        return json.loads(out)
    except (UnicodeError, ValueError):
        return {'status': 'error'}


def valid(candidate, limit, validate=True):
    if not isinstance(candidate, str) or len(candidate) > limit or not candidate.strip():
        return False
    try:
        candidate.encode('utf-8')
    except UnicodeEncodeError:
        return False
    return not validate or invoke('validate_input', candidate).get('value') is True


def generated(function, *args):
    outcome = invoke(function, *args)
    values = outcome.get('value')
    if not isinstance(values, list):
        return [], outcome['status'] if outcome['status'] != 'ok' else 'invalid_result'
    return values, 'ok'


def materialize():
    stats = {'small_pools': [], 'metamorphic_pools': []}
    pools, pairs = [], []
    seen_pairs = set()
    for seed in req['pool_seeds']:
        n = req['cases_per_pool']
        raw, status = generated('gen_small', seed, n)
        accepted = {}
        for inp in raw[:n]:
            if isinstance(inp, str) and inp not in accepted and valid(inp, SMALL_LIMIT, req['validator_public_ok']):
                accepted[inp] = None
        cases = []
        for inp in sorted(accepted, key=len):
            ref = invoke('reference_small', inp) if req['oracle_enabled'] else None
            cases.append({'input': inp, 'reference': ref})
        pools.append(cases)
        stats['small_pools'].append({'seed': seed, 'generated': len(raw), 'accepted': len(cases),
                                     'generator_status': status})

        raw, status = generated('metamorphic_pairs', seed, n)
        accepted_count = 0
        for pair in raw[:n]:
            if not isinstance(pair, list) or len(pair) != 4:
                continue
            post_id, relation, first, second = pair
            if (not isinstance(post_id, str) or not re.fullmatch(POST_ID, post_id) or relation not in RELATIONS
                    or not isinstance(first, str) or not isinstance(second, str)):
                continue
            key = tuple(pair)
            if key in seen_pairs or not (valid(first, SMALL_LIMIT) and valid(second, SMALL_LIMIT)):
                continue
            seen_pairs.add(key)
            accepted_count += 1
            refs = [invoke('reference_small', inp) for inp in (first, second)] if req['oracle_enabled'] else []
            pairs.append({'post_id': post_id, 'relation': relation, 'input1': first, 'input2': second,
                          'references': refs})
        stats['metamorphic_pools'].append({'seed': seed, 'generated': len(raw), 'accepted': accepted_count,
                                           'generator_status': status})

    raw, status = generated('gen_stress', req['stress_seed'])
    stress = []
    for inp in raw[:8]:
        if inp not in stress and valid(inp, STRESS_LIMIT):
            stress.append(inp)
            if len(stress) == 2:
                break
    stats['stress'] = {'seed': req['stress_seed'], 'generated': len(raw), 'accepted': len(stress),
                       'generator_status': status}
    return {'small_pools': pools, 'metamorphic_pairs': pairs, 'stress_inputs': stress, 'stats': stats}


req = json.load(sys.stdin)
if req['operation'] == 'calibrate':
    response = [{
        'validation': invoke('validate_input', case['input']),
        'property': invoke('check_postconditions', case['input'], case['output']),
        'reference': invoke('reference_small', case['input']),
    } for case in req['public_cases']]
elif req['operation'] == 'materialize':
    response = materialize()
elif req['operation'] == 'properties':
    response = [invoke('check_postconditions', case['input'], case['output']) for case in req['cases']]
else:
    raise ValueError('Unknown module operation')
json.dump(response, sys.stdout)
''')

_CANDIDATE_DISPATCHER = _CONTAINER_SUPPORT + r'''
import base64
from pathlib import Path


req = json.load(sys.stdin)
source = base64.b64decode(req['source_b64'], validate=True)
response = []
for case in req['cases']:
    with tempfile.TemporaryDirectory(dir='/tmp') as work:
        path = Path(work) / 'solution.py'
        path.write_bytes(source)
        status, out, err = capture([sys.executable, '-I', str(path)], case['input'].encode(),
                                   case['timeout'], cwd=work)
    response.append({'status': status, 'output': out.decode('utf-8', 'replace'),
                     'stderr': err.decode('utf-8', 'replace')})
json.dump(response, sys.stdout)
'''


def _positive_timeout(value):
    if not math.isfinite(value) or value <= 0:
        raise ValueError('D2 timeouts must be finite and positive')


def _budget(call_count, per_call):
    return max(25.0, 12.0 + call_count * (per_call + 0.1))


def _outcome_batch(data, count):
    if (not isinstance(data, list) or len(data) != count
            or any(not isinstance(item, dict) for item in data)):
        raise D2SandboxError('D2 dispatcher returned an invalid result batch')
    return data


def _post_violations(outcome):
    value = outcome.get('value') if outcome.get('status') == 'ok' else None
    if isinstance(value, list) and all(
        isinstance(item, (list, tuple)) and len(item) == 2
        and isinstance(item[0], str) and _POST_ID.fullmatch(item[0])
        and isinstance(item[1], str) and bool(item[1].strip()) for item in value
    ):
        return value
    return None


def _reference_value(outcome):
    value = outcome.get('value') if outcome and outcome.get('status') == 'ok' else None
    return value if isinstance(value, str) else None


def _relation_holds(relation, first, second):
    if relation == 'equal':
        return outputs_match(first, second)
    if relation == 'same_yes_no':
        first, second = first.strip().casefold(), second.strip().casefold()
        return first in ('yes', 'no') and first == second
    if relation in ('le', 'ge'):
        left_tokens, right_tokens = first.split(), second.split()
        if len(left_tokens) == len(right_tokens) == 1:
            try:
                left, right = Decimal(left_tokens[0]), Decimal(right_tokens[0])
                return (left.is_finite() and right.is_finite()
                        and (left <= right if relation == 'le' else left >= right))
            except InvalidOperation:
                pass
    return False


def compile_d2_bank(bundle_artifact, public_cases, *, pool_seeds=(101, 202, 303),
                    cases_per_pool=15, stress_seed=909, per_case_timeout=1.5, docker_runner=None):
    """Calibrate on public examples, then materialize a JSON-serializable bank."""
    _positive_timeout(per_case_timeout)
    if not isinstance(cases_per_pool, int) or cases_per_pool < 0:
        raise ValueError('cases_per_pool must be a non-negative integer')
    pool_seeds = list(pool_seeds)
    public_cases = [{'input': case['input'], 'output': case['output']} for case in public_cases]
    code = bundle_artifact['module_code']
    _check_module(code)
    runner = docker_runner if docker_runner is not None else run_in_throwaway_docker
    base = {'module_code': code, 'per_case_timeout': per_case_timeout}
    calibration = _outcome_batch(runner(
        _MODULE_DISPATCHER, base | {'operation': 'calibrate', 'public_cases': public_cases},
        timeout=_budget(3 * len(public_cases), per_case_timeout),
    ), len(public_cases))

    public = dict.fromkeys((
        'cases', 'validator_accepted', 'property_passed', 'reference_matched',
        'reference_mismatched', 'reference_none', 'reference_timeout', 'reference_error',
    ), 0)
    public['cases'] = len(public_cases)
    for case, outcomes in zip(public_cases, calibration):
        validation = outcomes['validation']
        public['validator_accepted'] += validation.get('status') == 'ok' and validation.get('value') is True
        public['property_passed'] += _post_violations(outcomes['property']) == []
        ref = outcomes['reference']
        reference = _reference_value(ref)
        if reference is not None:
            key = 'reference_matched' if outputs_match(reference, case['output']) else 'reference_mismatched'
        elif ref.get('status') == 'timeout':
            key = 'reference_timeout'
        elif ref.get('status') == 'ok' and ref.get('value') is None:
            key = 'reference_none'
        else:
            key = 'reference_error'
        public[key] += 1

    validator_ok = public['validator_accepted'] == public['cases']
    property_enabled = public['property_passed'] == public['cases']
    oracle_enabled = public['reference_matched'] >= 1 and public['reference_mismatched'] == 0
    generated = runner(
        _MODULE_DISPATCHER,
        base | {'operation': 'materialize', 'pool_seeds': pool_seeds, 'cases_per_pool': cases_per_pool,
                'stress_seed': stress_seed, 'validator_public_ok': validator_ok, 'oracle_enabled': oracle_enabled},
        timeout=_budget(len(pool_seeds) * (2 + 6 * cases_per_pool) + 9, per_case_timeout),
    )

    pools = [
        [{'input': case['input'], 'ref_output': _reference_value(case['reference'])} for case in pool]
        for pool in generated['small_pools']
    ]
    pairs = []
    mismatched = unverified = 0
    for pair in generated['metamorphic_pairs']:
        if oracle_enabled:
            first, second = map(_reference_value, pair['references'])
            if first is None or second is None:
                unverified += 1
                continue
            if not _relation_holds(pair['relation'], first, second):
                mismatched += 1
                continue
        pairs.append({key: pair[key] for key in ('post_id', 'relation', 'input1', 'input2')})

    stress = generated['stress_inputs']
    stats = generated['stats'] | {
        'public': public,
        'oracle_labeled_small': sum(case['ref_output'] is not None for pool in pools for case in pool),
        'metamorphic': {'accepted': len(pairs), 'reference_mismatched': mismatched,
                        'reference_unavailable': unverified},
    }
    return {
        'schema': 'csc2108-d2-bank-v1', 'task_id': bundle_artifact['task_id'],
        'statement_sha256': bundle_artifact['statement_sha256'], 'prompt_sha256': bundle_artifact.get('prompt_sha256'),
        'contract_md': bundle_artifact['contract_md'], 'module_code': code,
        'validator_public_ok': validator_ok, 'property_enabled': property_enabled,
        'oracle_enabled': oracle_enabled, 'stress_enabled': bool(stress),
        'pool_seeds': pool_seeds, 'small_pools': pools, 'metamorphic_pairs': pairs,
        'stress_inputs': stress, 'compilation_stats': stats,
    }


def evaluate_candidate_against_bank(source_bytes, bank, *, mode='oracle', pool_index=0,
                                    small_timeout=2.0, stress_timeout=4.0, docker_runner=None):
    """Evaluate one candidate in one mode and report the smallest observed failure."""
    if mode not in _MODES:
        raise ValueError(f'Unknown D2 mode: {mode}')
    _positive_timeout(small_timeout)
    _positive_timeout(stress_timeout)
    started = time.monotonic()
    runner = docker_runner if docker_runner is not None else run_in_throwaway_docker
    pools = bank['small_pools']
    small = pools[pool_index % len(pools)] if pools else []
    stress = bank['stress_inputs'] if bank['stress_enabled'] else []
    pairs = bank['metamorphic_pairs'] if mode == 'property' else []
    cases = {}
    for inp in stress:
        cases[inp] = ('stress', stress_timeout)
    for inp in (case['input'] for case in small):
        cases[inp] = ('small', small_timeout)
    for pair in pairs:
        for inp in (pair['input1'], pair['input2']):
            cases.setdefault(inp, ('metamorphic', small_timeout))

    counts = dict.fromkeys(_COUNT_KEYS, 0)
    counts['small_ran'] = len(small)
    counts['stress_ran'] = len(stress)
    failures = []
    results = {}
    if cases:
        request_cases = [{'input': inp, 'timeout': timeout} for inp, (_, timeout) in cases.items()]
        payload = {'operation': 'candidate', 'cases': request_cases,
                   'source_b64': base64.b64encode(source_bytes).decode('ascii')}
        responses = _outcome_batch(runner(
            _CANDIDATE_DISPATCHER, payload, timeout=max(25.0, 12.0 + sum(t + 0.1 for _, t in cases.values())),
        ), len(cases))
        for (inp, (suite, timeout)), result in zip(cases.items(), responses):
            status = result.get('status')
            if status not in ('ok', 'error', 'timeout'):
                raise D2SandboxError(f'Unexpected D2 candidate status: {status!r}')
            results[inp] = result
            if status != 'ok':
                reason = 'TLE' if status == 'timeout' else 'RE'
                counts[reason.lower()] += 1
                failures.append({'reason': reason, 'suite': suite, 'input': inp, 'timeout': timeout,
                                 'output': result.get('output', ''), 'detail': result.get('stderr', '')})

    if mode == 'property':
        if bank['property_enabled']:
            property_cases = [{'input': inp, 'output': result['output']} for inp, result in results.items()
                              if result['status'] == 'ok']
            if property_cases:
                _check_module(bank['module_code'])
                payload = {'operation': 'properties', 'module_code': bank['module_code'],
                           'cases': property_cases, 'per_case_timeout': small_timeout}
                outcomes = _outcome_batch(runner(
                    _MODULE_DISPATCHER, payload, timeout=_budget(len(property_cases), small_timeout),
                ), len(property_cases))
                for case, outcome in zip(property_cases, outcomes):
                    violations = _post_violations(outcome)
                    if violations:
                        post_id, detail = violations[0]
                        counts['post_fail'] += 1
                        failures.append({'reason': 'postcondition', 'suite': cases[case['input']][0],
                                         **case, 'post_id': post_id, 'detail': detail})

        for pair in pairs:
            first, second = (results[pair[key]] for key in ('input1', 'input2'))
            if first['status'] == second['status'] == 'ok':
                counts['meta_ran'] += 1
                if not _relation_holds(pair['relation'], first['output'], second['output']):
                    counts['meta_fail'] += 1
                    failures.append({'reason': 'metamorphic', 'suite': 'metamorphic',
                                     'input': pair['input1'], 'input2': pair['input2'],
                                     'output': first['output'], 'output2': second['output'],
                                     'post_id': pair['post_id'], 'relation': pair['relation']})

    if mode == 'oracle' and bank['oracle_enabled']:
        for case in small:
            inp, expected = case['input'], case['ref_output']
            result = results[inp]
            if expected is not None and result['status'] == 'ok' and not outputs_match(result['output'], expected):
                counts['oracle_mismatch'] += 1
                failures.append({'reason': 'oracle_mismatch', 'suite': 'small', 'input': inp,
                                 'output': result['output'], 'expected_output': expected})

    first_failure = min(failures, key=lambda f: max(len(f['input']), len(f.get('input2', ''))), default=None)
    return {'mode': mode, 'passed': first_failure is None, 'first_failure': first_failure,
            'counts': counts, 'seconds': round(time.monotonic() - started, 3)}


def _excerpt(text, size=500):
    if len(text) <= size:
        return repr(text)
    return f'{text[:size]!r} … ({len(text)} characters total)'


def _render_failure(failure):
    lines = ['[Contract verification gate — supplementary, NOT verified; judge-public above is authoritative]',
             f"Input: {_excerpt(failure['input'])}", f"Your output: {_excerpt(failure['output'])}"]
    reason = failure['reason']
    if reason == 'oracle_mismatch':
        lines.append(f"Expected output: {_excerpt(failure['expected_output'])}")
    elif reason == 'metamorphic':
        lines += [f"Second input: {_excerpt(failure['input2'])}",
                  f"Your second output: {_excerpt(failure['output2'])}",
                  f"Violated {failure['post_id']}: {failure['relation']} (first output, second output)."]
    elif reason == 'postcondition':
        lines.append(f"Violated {failure['post_id']}: {_excerpt(failure['detail'])}")
    elif reason == 'TLE':
        lines.append(f"TLE after {failure['timeout']:g} seconds.")
    else:
        lines.append(f"RE: {_excerpt(failure['detail'])}")
    lines.append('Fix /workspace/solution.py and retest with python -I /public/check.py.')
    return '\n'.join(lines)


class D2GateChecker:
    """Rotate seed pools after each authoritative public pass."""

    def __init__(self, bank, mode='oracle', trigger='public_pass_only', small_timeout=2.0,
                 stress_timeout=4.0, docker_runner=None):
        if mode not in _MODES:
            raise ValueError(f'Unknown D2 mode: {mode}')
        if trigger != 'public_pass_only':
            raise ValueError(f'Unknown D2 trigger: {trigger}')
        self.bank = bank
        self.mode = mode
        self.trigger = trigger
        self.small_timeout = small_timeout
        self.stress_timeout = stress_timeout
        self.docker_runner = docker_runner
        self.runs = []

    def on_public_pass(self, source_bytes, digest):
        run_index = len(self.runs)
        pool_index = run_index % (len(self.bank['small_pools']) or 1)
        started = time.monotonic()
        try:
            result = evaluate_candidate_against_bank(
                source_bytes, self.bank, mode=self.mode, pool_index=pool_index,
                small_timeout=self.small_timeout, stress_timeout=self.stress_timeout, docker_runner=self.docker_runner,
            )
        except (D2SandboxError, subprocess.TimeoutExpired) as error:
            detail = (f'D2 Docker dispatcher exceeded its {error.timeout:g} second deadline'
                      if isinstance(error, subprocess.TimeoutExpired) else str(error))
            result = {'mode': self.mode, 'passed': None, 'first_failure': None, 'counts': None,
                      'seconds': round(time.monotonic() - started, 3), 'sandbox_error': detail}
        entry = {'seq': run_index + 1, 'source_sha256': digest, 'pool_index': pool_index, **result}
        self.runs.append(entry)
        return entry, _render_failure(entry['first_failure']) if entry['first_failure'] else ''

    def summary(self):
        passed = sum(entry['passed'] is True for entry in self.runs)
        failures = sum(entry['passed'] is False for entry in self.runs)
        return {'mode': self.mode, 'trigger': self.trigger, 'checks': len(self.runs),
                'passed': passed, 'failed': failures, 'unavailable': len(self.runs) - passed - failures,
                'runs': list(self.runs)}


def evaluate_bank_on_mutant_pool_task(bank, task_entry, *, include_public_fail_mutants=False,
                                      pool_index=0, small_timeout=2.0, stress_timeout=4.0,
                                      docker_runner=None):
    """Measure the three ablations using a common seed pool from the precompiled bank."""
    if bank['task_id'] != task_entry['task_id']:
        raise ValueError('The D2 bank and mutant pool must describe the same task')
    groups = ['references', 'public_pass_mutants']
    if include_public_fail_mutants:
        groups.append('public_fail_mutants')

    modes = {}
    for mode in _MODES:
        mutants = {group: {'total': 0, 'killed': 0, 'survived': 0, 'kill_rate': None,
                           'by_reason': dict.fromkeys(_FAILURES, 0), 'by_hidden_verdict': {}, 'kills': []}
                   for group in groups if group != 'references'}
        modes[mode] = {'references': {'total': 0, 'false_rejected': 0, 'false_rejection_rate': None,
                                      'false_rejections': []}, **mutants}

    for group in groups:
        for submission in task_entry.get(group, []):
            sha = submission['submission_sha256']
            source = (REPO / submission['rel_path']).read_bytes()
            if sha256_bytes(source) != sha:
                raise ValueError(f"Mutant pool digest mismatch for {submission['rel_path']}")
            for mode in _MODES:
                result = evaluate_candidate_against_bank(
                    source, bank, mode=mode, pool_index=pool_index, small_timeout=small_timeout,
                    stress_timeout=stress_timeout, docker_runner=docker_runner,
                )
                stats = modes[mode][group]
                stats['total'] += 1
                failure = result['first_failure']
                record = {'submission_sha256': sha, 'counterexample': failure}
                if group == 'references':
                    if failure is not None:
                        stats['false_rejected'] += 1
                        stats['false_rejections'].append(record)
                    continue

                verdict = submission['dominant_verdict']
                by_verdict = stats['by_hidden_verdict'].setdefault(
                    verdict, {'total': 0, 'killed': 0, 'kill_rate': None, 'by_reason': dict.fromkeys(_FAILURES, 0)},
                )
                by_verdict['total'] += 1
                if failure is not None:
                    for bucket in (stats, by_verdict):
                        bucket['killed'] += 1
                        bucket['by_reason'][failure['reason']] += 1
                    stats['kills'].append(record | {'hidden_verdict': verdict})
                else:
                    stats['survived'] += 1

    for by_group in modes.values():
        refs = by_group['references']
        if refs['total']:
            refs['false_rejection_rate'] = refs['false_rejected'] / refs['total']
        for group in groups[1:]:
            stats = by_group[group]
            for bucket in [stats, *stats['by_hidden_verdict'].values()]:
                if bucket['total']:
                    bucket['kill_rate'] = bucket['killed'] / bucket['total']
                bucket['kill_rate_by_reason'] = {
                    reason: count / bucket['total'] if bucket['total'] else None
                    for reason, count in bucket['by_reason'].items()
                }
    return {'task_id': bank['task_id'], 'pool_index': pool_index, 'modes': modes}
