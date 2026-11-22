"""Reference output-comparison rules, validated offline. NOT used to score any experiment.

Judge 0.2.1 stays the scorer of record. Its comparator is loaded here from the frozen judge source
(``judge/container/judge.py``) by AST extraction, so tests exercise the exact deployed code on every host
(the judge module itself imports Linux-only modules). The other rules show what a future, versioned judge
would need for the categories ``output_semantics`` excludes today:

* ``tolerance_match``        AtCoder "absolute or relative error at most eps" per numeric token;
* ``case_insensitive_match`` exact rule after case folding;
* task-specific validators   for multiple-answer tasks (``VALIDATORS``), which need the input as well.

Adopting any of these changes scoring, so it would be a new judge version introduced before a cohort is
frozen and never applied to results that were already scored.
"""
import ast
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path

from .common import REPO

JUDGE_SOURCE = REPO / 'judge/container/judge.py'
_FROZEN_NAMES = ('_stripped_lines', '_decimals', 'outputs_match')


def frozen_comparator(path=JUDGE_SOURCE):
    """``outputs_match`` exactly as deployed in judge 0.2.1 (plus the version string it ships with)."""
    tree = ast.parse(Path(path).read_text(encoding='utf-8'))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in _FROZEN_NAMES]
    version = next(n.value.value for n in tree.body if isinstance(n, ast.Assign)
                   and getattr(n.targets[0], 'id', None) == 'JUDGE_VERSION')
    namespace = {'Decimal': Decimal, 'InvalidOperation': InvalidOperation}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)  # judge's own code
    return namespace['outputs_match'], version


outputs_match, JUDGE_VERSION = frozen_comparator()


def _lines(text):
    return [line.strip() for line in text.strip().split('\n')]


def _number(token):
    try:
        return Fraction(Decimal(token))
    except (InvalidOperation, ValueError):
        return None


def tolerance_match(actual, expected, eps):
    """Accept a token if identical, or if both are numbers with |a-b| <= eps or |a-b| <= eps*|b|."""
    eps = Fraction(eps)
    got, want = _lines(actual), _lines(expected)
    if len(got) != len(want):
        return False
    for a_line, b_line in zip(got, want):
        a_tokens, b_tokens = a_line.split(), b_line.split()
        if len(a_tokens) != len(b_tokens):
            return False
        for a, b in zip(a_tokens, b_tokens):
            if a == b:
                continue
            x, y = _number(a), _number(b)
            if x is None or y is None:
                return False
            if abs(x - y) > eps and abs(x - y) > eps * abs(y):
                return False
    return True


def case_insensitive_match(actual, expected):
    return outputs_match(actual.casefold(), expected.casefold())


def xor_min_sum_valid(case_input, expected, actual):
    """abc396_e validator: -1 iff no good sequence; otherwise N non-negative integers satisfying every
    A_X xor A_Y = Z whose sum equals the reference (minimum) sum. Any such sequence is accepted."""
    head, *rest = case_input.split('\n', 1)
    n, m = map(int, head.split())
    numbers = list(map(int, rest[0].split())) if rest else []
    triples = [numbers[i:i + 3] for i in range(0, 3 * m, 3)]
    want, got = expected.split(), actual.split()
    if want == ['-1'] or got == ['-1']:
        return want == got
    if len(got) != n or not all(t.lstrip('-').isdigit() for t in got):
        return False
    values = [int(t) for t in got]
    if any(v < 0 for v in values):
        return False
    if any(values[x - 1] ^ values[y - 1] != z for x, y, z in triples):
        return False
    return sum(values) == sum(int(t) for t in want)


VALIDATORS = {'lcb-atcoder-abc396_e': xor_min_sum_valid}


def compare(category, actual, expected, *, eps=None, task_id=None, case_input=None):
    """Dispatch by reviewed category. ``exact`` is the frozen judge rule, unchanged."""
    if category == 'exact':
        return outputs_match(actual, expected)
    if category == 'tolerance':
        if eps is None:
            raise ValueError('tolerance comparison needs the stated eps')
        return tolerance_match(actual, expected, eps)
    if category == 'case_insensitive':
        return case_insensitive_match(actual, expected)
    if category == 'multiple_answers':
        if task_id not in VALIDATORS:
            raise NotImplementedError(f'no validator for multiple-answer task {task_id}; the task is unsupported')
        return VALIDATORS[task_id](case_input, expected, actual)
    raise NotImplementedError(f'category {category} is not a batch stdin/stdout comparison')
