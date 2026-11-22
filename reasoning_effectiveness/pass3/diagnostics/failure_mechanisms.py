"""Observable failure mechanisms of the frozen local agent (truncation, identical rewrites), from preserved runs.

usage (repository root):
  python -m reasoning_effectiveness.pass3.diagnostics.failure_mechanisms OUT.json STUDY[@BATCH,...] ...

Reads, per Qwen run: every raw model response (``ollama-responses.json``: text, done_reason, eval_count), the
public-test record (``attempts.jsonl``) and the run record. It never infers hidden reasoning: every measure is
a property of emitted text or of judged candidates.

Per response:
  * truncated (done_reason == 'length' at the 4,096-token cap) and where the text was when it stopped:
    ``prose`` (no command fence opened), ``in_block`` (fence opened, never closed);
  * in-block composition of the heredoc body: code lines, comment lines, docstring/string-literal lines, blank;
  * whether a parsable program prefix existed (longest line prefix that ``ast.parse`` accepts) and whether that
    prefix already reads input and prints (a "complete-looking" program lost to truncation).
Per run:
  * identical rewrites: a write of /workspace/solution.py whose content hash equals a candidate that had already
    FAILED a public test; consecutive identical writes; exact repeats of an earlier assistant response;
  * public tests, failures, and the first response's length.
Output: per-run rows and per-response rows (no program text), plus aggregates by study cohort and condition.
"""
import ast
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

FENCE = re.compile(r'```(?:mswea_bash_command|bash)\s*\n')
HEREDOC = re.compile(r"(?:cat|tee)\s*>?\s*/workspace/solution\.py\s*<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n(.*?)(?:\n\1\s*(?:\n|$)|$)", re.S)
READS = re.compile(r'\binput\s*\(|sys\.stdin|open\(0\)|readline|read\(\)')
PRINTS = re.compile(r'\bprint\s*\(|sys\.stdout\.write')


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def composition(body):
    counts = Counter()
    in_string = None
    for raw in body.split('\n'):
        line = raw.strip()
        if in_string:
            counts['docstring'] += 1
            if in_string in line:
                in_string = None
            continue
        if not line:
            counts['blank'] += 1
        elif line.startswith('#'):
            counts['comment'] += 1
        elif line.startswith(('"""', "'''")):
            quote = line[:3]
            counts['docstring'] += 1
            if line.count(quote) == 1:
                in_string = quote
        else:
            counts['code'] += 1
    return dict(counts)


def parsable_prefix(body):
    lines = body.split('\n')
    for end in range(len(lines), 0, -1):
        try:
            ast.parse('\n'.join(lines[:end]))
            return end, '\n'.join(lines[:end])
        except (SyntaxError, ValueError, RecursionError):
            continue
    return 0, ''


def response_row(text, done_reason, tokens):
    fence = FENCE.search(text)
    row = {'tokens': tokens, 'truncated': done_reason == 'length', 'chars': len(text),
           'prose_chars_before_fence': fence.start() if fence else len(text), 'fence_opened': bool(fence)}
    block = text[fence.end():] if fence else ''
    row['fence_closed'] = bool(fence) and '```' in block
    row['where'] = 'complete' if row['fence_closed'] else ('in_block' if fence else 'prose')
    heredoc = HEREDOC.search(block) if fence else None
    if heredoc:
        body = heredoc.group(2)
        row['writes_solution'] = True
        row['composition'] = composition(body)
        n, prefix = parsable_prefix(body)
        row['parsable_prefix_lines'] = n
        row['body_lines'] = body.count('\n') + 1
        row['prefix_reads_and_prints'] = bool(READS.search(prefix) and PRINTS.search(prefix))
        row['body_sha256'] = sha(body + '\n')  # a heredoc writes the body plus a final newline
    else:
        row['writes_solution'] = False
    return row


def load_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def run_rows(run_dir, cohort):
    record = json.loads((run_dir / 'result.json').read_text(encoding='utf-8'))
    if str(record.get('coding_model', 'qwen')).startswith('frontier') or record.get('coder'):
        return None, []
    agents = sorted(run_dir.glob('agent-*'))
    if not agents or not (agents[0] / 'ollama-responses.json').exists():
        return None, []
    responses = json.loads((agents[0] / 'ollama-responses.json').read_text(encoding='utf-8'))
    attempts = load_jsonl(run_dir / 'attempts.jsonl')
    failed = {a.get('source_sha256') for a in attempts if (a.get('result') or {}).get('status') == 'candidate_failure'}
    rows, texts, writes = [], [], []
    tested_failed_so_far = set()
    attempt_iter = iter(attempts)
    for index, response in enumerate(responses):
        text = (response.get('message') or {}).get('content') or ''
        row = response_row(text, response.get('done_reason'), response.get('eval_count'))
        row.update(index=index, run=f'{cohort}/{run_dir.parent.name}/{run_dir.name}', condition=record.get('condition'))
        row['exact_repeat_of_earlier_response'] = text in texts
        texts.append(text)
        if row.get('writes_solution') and row['where'] == 'complete':
            writes.append(row['body_sha256'])
        rows.append(row)
    # A written body equals a judged candidate when the harness snapshot hash matches (same bytes on disk).
    identical_failed = sum(1 for h in writes if h in failed)
    consecutive = sum(1 for a, b in zip(writes, writes[1:]) if a == b)
    trunc = [r for r in rows if r['truncated']]
    run = {
        'run': f'{cohort}/{run_dir.parent.name}/{run_dir.name}', 'cohort': cohort, 'batch': run_dir.parent.name,
        'task_id': record.get('task_id'), 'condition': record.get('condition'), 'seed': record.get('seed'),
        'aci': bool(record.get('aci')), 'probe': run_dir.parent.name.startswith('probe'),
        'variant': (json.loads((run_dir / 'spec.json').read_text(encoding='utf-8')).get('variant')
                    if (run_dir / 'spec.json').exists() else None),
        'responses': len(rows), 'truncated': len(trunc),
        'truncated_where': dict(Counter(r['where'] for r in trunc)),
        'truncated_with_parsable_reading_printing_prefix': sum(1 for r in trunc if r.get('prefix_reads_and_prints')),
        'first_response_tokens': rows[0]['tokens'] if rows else None,
        'first_response_truncated': bool(rows and rows[0]['truncated']),
        'public_tests': len(attempts), 'public_failures': sum(1 for a in attempts
                                                               if (a.get('result') or {}).get('status') == 'candidate_failure'),
        'distinct_tested_candidates': len({a.get('source_sha256') for a in attempts}),
        'retests_of_already_failed_candidate': sum(1 for a, seen in _seen(attempts) if seen),
        'writes': len(writes), 'rewrites_identical_to_failed_candidate': identical_failed,
        'consecutive_identical_writes': consecutive,
        'exact_repeated_responses': sum(1 for r in rows if r['exact_repeat_of_earlier_response']),
        'exit_status': record.get('exit_status'), 'n_actions': record.get('n_actions'),
    }
    return run, rows


def _seen(attempts):
    failed = set()
    for a in attempts:
        h = a.get('source_sha256')
        yield a, h in failed
        if (a.get('result') or {}).get('status') == 'candidate_failure':
            failed.add(h)


def aggregate(runs, responses):
    out = defaultdict(lambda: Counter())
    for run in runs:
        key = f"{run['cohort']}|{run['condition']}" + ('+aci' if run['aci'] else '') + ('+probe' if run['probe'] else '')
        c = out[key]
        c['runs'] += 1
        for k in ('responses', 'truncated', 'truncated_with_parsable_reading_printing_prefix', 'public_tests',
                  'public_failures', 'retests_of_already_failed_candidate', 'writes',
                  'rewrites_identical_to_failed_candidate', 'consecutive_identical_writes', 'exact_repeated_responses'):
            c[k] += run[k] or 0
        c['runs_first_response_truncated'] += run['first_response_truncated']
        c['runs_with_any_truncation'] += run['truncated'] > 0
        c['runs_never_public_tested'] += run['public_tests'] == 0
        c['runs_with_identical_failed_rewrite'] += run['rewrites_identical_to_failed_candidate'] > 0
        for where, n in run['truncated_where'].items():
            c['truncated_' + where] += n
    comp = defaultdict(Counter)
    for r in responses:
        if r['truncated'] and r.get('composition'):
            for k, v in r['composition'].items():
                comp[r['condition']][k] += v
    return {k: dict(v) for k, v in out.items()}, {k: dict(v) for k, v in comp.items()}


def main(out, *specs):
    runs, responses = [], []
    for spec in specs:
        study, _, batches = spec.partition('@')  # STUDY@batch1,batch2 (':' is a drive letter)
        study = Path(study)
        cohort = study.name.replace('reasoning-effectiveness', 'pass1').replace('pass1-pass', 'pass')
        wanted = batches.split(',') if batches else None
        for result in sorted(study.glob('runs/*/*/result.json')):
            if wanted and result.parent.parent.name not in wanted:
                continue
            if 'incomplete' in result.parent.name or result.parent.parent.name.startswith(('integration', 'b-')):
                continue
            try:
                run, rows = run_rows(result.parent, cohort)
            except Exception as error:  # report, never hide, a broken record
                runs.append({'run': str(result.parent), 'error': f'{type(error).__name__}: {error}'})
                continue
            if run:
                runs.append(run)
                responses += rows
    good = [r for r in runs if 'error' not in r]
    agg, comp = aggregate(good, responses)
    data = {'runs': runs, 'responses': responses, 'aggregate': agg, 'truncated_composition_by_condition': comp}
    Path(out).write_text(json.dumps(data, indent=1) + '\n', encoding='utf-8', newline='\n')
    for k in sorted(agg):
        print(k, json.dumps(agg[k]))
    print('truncated in-block composition:', json.dumps(comp))
    print(len(good), 'runs;', len(responses), 'responses;', len(runs) - len(good), 'errors')


if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:])
