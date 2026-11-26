"""Deterministic static AST, complexity, and constraint analyzer for Python candidates.

Inspired by CUDAnalyst (Chong et al., ICML'26): provides structured analyzer/profiler
signals alongside runtime failure reports without invoking any LLM.
"""
import ast
import re


_CONSTRAINT_PATTERNS = [
    # LaTeX / plain text upper bounds like 1 <= N <= 2 \times 10^5, N <= 10^{18}, N \le 500000
    re.compile(
        r'\b([A-Z][A-Za-z0-9_]{0,3})\s*(?:\\le|<=|≤)\s*'
        r'(?:(\d+)\s*(?:\\times|\*|x)\s*)?10\s*\^\s*\{?(\d+)\}?'
    ),
    re.compile(r'\b([A-Z][A-Za-z0-9_]{0,3})\s*(?:\\le|<=|≤)\s*([0-9][0-9,_]{3,})\b'),
    re.compile(r'\b([A-Z][A-Za-z0-9_]{0,3})\s*(?:\\le|<=|≤)\s*(\d+e\d+)\b', re.I),
]


def parse_constraint_scales(statement):
    """Extract likely upper-bound scales of main variables from the problem statement."""
    scales = {}
    if not statement:
        return scales
    # Pattern 1: a * 10^b
    for var, coeff, exp in _CONSTRAINT_PATTERNS[0].findall(statement):
        try:
            val = (int(coeff) if coeff else 1) * (10 ** int(exp))
            scales[var] = max(scales.get(var, 0), val)
        except ValueError:
            pass
    # Pattern 2: plain integer >= 1000
    for var, num_s in _CONSTRAINT_PATTERNS[1].findall(statement):
        try:
            val = int(num_s.replace(',', '').replace('_', ''))
            scales[var] = max(scales.get(var, 0), val)
        except ValueError:
            pass
    # Pattern 3: scientific notation
    for var, num_s in _CONSTRAINT_PATTERNS[2].findall(statement):
        try:
            val = int(float(num_s))
            scales[var] = max(scales.get(var, 0), val)
        except ValueError:
            pass
    return dict(sorted(scales.items(), key=lambda kv: (-kv[1], kv[0])))


def _loop_depth(node, depth=0):
    best = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.For, ast.AsyncFor, ast.While)):
            best = max(best, _loop_depth(child, depth + 1))
        elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            best = max(best, _loop_depth(child, depth + len(child.generators)))
        else:
            best = max(best, _loop_depth(child, depth))
    return best


def _find_recursive_functions(tree):
    recursive = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            calls = set()
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    if isinstance(sub.func, ast.Name):
                        calls.add(sub.func.id)
            if node.name in calls:
                recursive.append(node.name)
    return sorted(set(recursive))


def analyze_python_source(source_text, statement=''):
    """Return structured deterministic static analysis facts and risk flags."""
    scales = parse_constraint_scales(statement)
    max_scale = max(scales.values()) if scales else 0
    lines = source_text.splitlines()
    code_lines = [ln for ln in lines if ln.strip() and not ln.strip().startswith('#')]
    comment_lines = [ln for ln in lines if ln.strip().startswith('#')]

    facts = {
        'total_lines': len(lines),
        'code_lines': len(code_lines),
        'comment_lines': len(comment_lines),
        'syntax_ok': True,
        'syntax_error': None,
        'max_loop_depth': 0,
        'recursive_functions': [],
        'has_setrecursionlimit': 'setrecursionlimit' in source_text,
        'uses_fast_io': ('sys.stdin' in source_text or 'stdin.read' in source_text or 'stdin.buffer' in source_text),
        'uses_input_in_loop': False,
        'has_quadratic_list_ops_in_loop': [],
        'uses_float_ops': False,
        'constraint_scales': scales,
        'risk_flags': [],
    }
    try:
        tree = ast.parse(source_text)
    except SyntaxError as exc:
        facts['syntax_ok'] = False
        facts['syntax_error'] = f'line {exc.lineno}: {exc.msg}'
        facts['risk_flags'].append(f'SyntaxError at line {exc.lineno}: {exc.msg}')
        return facts

    facts['max_loop_depth'] = _loop_depth(tree)
    facts['recursive_functions'] = _find_recursive_functions(tree)

    # Walk loops for slow patterns
    quad_hits = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.While)):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    if isinstance(sub.func, ast.Name) and sub.func.id == 'input':
                        facts['uses_input_in_loop'] = True
                    if isinstance(sub.func, ast.Attribute) and sub.func.attr == 'pop':
                        if sub.args and isinstance(sub.args[0], ast.Constant) and sub.args[0].value == 0:
                            quad_hits.add('list.pop(0) inside loop')
                    if isinstance(sub.func, ast.Attribute) and sub.func.attr == 'insert':
                        if sub.args and isinstance(sub.args[0], ast.Constant) and sub.args[0].value == 0:
                            quad_hits.add('list.insert(0, ...) inside loop')
                    if isinstance(sub.func, ast.Name) and sub.func.id == 'sum':
                        if sub.args and isinstance(sub.args[0], ast.Subscript) and isinstance(sub.args[0].slice, ast.Slice):
                            quad_hits.add('sum(slice) inside loop')
                if isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.Div):
                    facts['uses_float_ops'] = True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ('float', 'sqrt'):
            facts['uses_float_ops'] = True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'sqrt':
            facts['uses_float_ops'] = True

    facts['has_quadratic_list_ops_in_loop'] = sorted(quad_hits)

    # Synthesize actionable risk flags
    if facts['recursive_functions'] and not facts['has_setrecursionlimit'] and max_scale >= 1000:
        facts['risk_flags'].append(
            f"Recursion in {facts['recursive_functions']} without sys.setrecursionlimit() "
            f"(statement max scale ~{max_scale:,}); risk of RecursionError on deep inputs."
        )
    if facts['max_loop_depth'] >= 2 and max_scale >= 50000:
        facts['risk_flags'].append(
            f"Nested loops of depth {facts['max_loop_depth']} with statement scale up to {max_scale:,}; "
            "verify time complexity is sub-quadratic (avoid O(N^2) TLE)."
        )
    if facts['uses_input_in_loop'] and not facts['uses_fast_io'] and max_scale >= 100000:
        facts['risk_flags'].append(
            f"Repeated input() inside loop without sys.stdin.read/buffer at scale {max_scale:,}; potential I/O bottleneck."
        )
    for hit in facts['has_quadratic_list_ops_in_loop']:
        facts['risk_flags'].append(f'Potential O(N^2) list operation: {hit}.')
    if facts['uses_float_ops'] and max_scale >= 10**12:
        facts['risk_flags'].append(
            f'Floating-point division/sqrt detected with large integer scale ({max_scale:,}); '
            'risk of 53-bit float precision loss (prefer integer arithmetic / math.isqrt).'
        )
    return facts


def format_static_summary(facts, public_result=None):
    """Render a compact, structured analyzer summary suitable for E2 evidence packets."""
    lines = []
    if not facts.get('syntax_ok'):
        lines.append(f"- Syntax error: {facts.get('syntax_error')}")
        return '\n'.join(lines)
    scales = facts.get('constraint_scales') or {}
    scale_str = ', '.join(f'{k}<={v:,}' for k, v in list(scales.items())[:5]) or 'none parsed'
    lines.append(
        f"- Structure: {facts['code_lines']} code lines ({facts['comment_lines']} comments), "
        f"max loop depth {facts['max_loop_depth']}, "
        f"recursive={facts['recursive_functions'] or 'none'} "
        f"(setrecursionlimit={facts['has_setrecursionlimit']})."
    )
    lines.append(f"- Parsed statement scales: {scale_str}.")
    if public_result:
        cases = public_result.get('cases') or []
        timings = [
            f"{c.get('name')}:{c.get('verdict')}({c.get('time_s', c.get('elapsed_s', '?'))}s)"
            for c in cases[:6]
        ]
        if timings:
            lines.append('- Public case timings: ' + ', '.join(timings) + '.')
    flags = facts.get('risk_flags') or []
    if flags:
        lines.append('- Static risk flags:')
        for fl in flags:
            lines.append(f'  * {fl}')
    else:
        lines.append('- Static risk flags: none detected by lightweight AST check.')
    return '\n'.join(lines)
