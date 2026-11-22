"""How does Qwen act on a delivered E message? Structural change versus paraphrase (observable text only).

usage (repository root):  python -m reasoning_effectiveness.pass3.diagnostics.e_uptake OUT.json STUDY[@BATCH,...] ...

For every E run whose diagnosis (or probe message) was delivered:
  * the failed candidate at the trigger: the program inside the evidence packet (delimited DATA block);
  * the first program Qwen writes after the delivered message (first complete heredoc to solution.py);
  * structural change: changed-line ratio (difflib), a normalized AST dump identical or not, and the change in
    number of loops / function definitions / imports;
  * vocabulary uptake: the fraction of the message's distinctive words (length >= 6, not in the statement) that
    appear in Qwen's next response, separated into code-comment lines and code lines;
  * outcome fields: public pass after the message, hidden status (when evaluated).
Programs are never copied into the output; only measurements are.
"""
import ast
import difflib
import json
import re
import sys
from pathlib import Path

from reasoning_effectiveness.pass3.diagnostics.failure_mechanisms import FENCE, HEREDOC

WORD = re.compile(r'[A-Za-z_][A-Za-z_]{5,}')


def packet_program(user_message, nonce):
    """The tested program between <<<DATA-{nonce} program>>> and <<<END-DATA-{nonce}>>> (diagnosis.evidence_packet)."""
    match = re.search(r'<<<DATA-' + re.escape(nonce) + r' program>>>\n(.*?)\n<<<END-DATA-' + re.escape(nonce) + '>>>',
                      user_message, re.S)
    return match.group(1) + '\n' if match else None


def shape(source):
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None
    nodes = list(ast.walk(tree))
    return {'loops': sum(isinstance(n, (ast.For, ast.While)) for n in nodes),
            'functions': sum(isinstance(n, ast.FunctionDef) for n in nodes),
            'imports': sorted({a.name.split('.')[0] for n in nodes if isinstance(n, (ast.Import, ast.ImportFrom))
                               for a in (n.names if isinstance(n, ast.Import) else [ast.alias(name=n.module or '')])}),
            'dump_sha': __import__('hashlib').sha256(ast.dump(tree).encode()).hexdigest()[:16]}


def main(out, *specs):
    rows = []
    for spec in specs:
        study, _, batches = spec.partition('@')
        study = Path(study)
        wanted = batches.split(',') if batches else None
        for diag in sorted(study.glob('runs/*/*/diagnosis/diagnosis.json')):
            run_dir = diag.parent.parent
            if wanted and run_dir.parent.name not in wanted:
                continue
            if run_dir.parent.name.startswith('integration'):
                continue
            data = json.loads(diag.read_text(encoding='utf-8'))
            record = data.get('record') or {}
            if not record.get('delivered'):
                continue
            packet = json.loads((diag.parent / 'packet.json').read_text(encoding='utf-8'))
            before = packet_program(packet['user_message'], packet['nonce'])
            statement = json.loads((study / 'bundles' / packet['task_id'] / 'task.json').read_text(encoding='utf-8'))['statement']
            message = (data.get('response') or {}).get('text') or ''
            agent = sorted(run_dir.glob('agent-*'))[0]
            messages = json.loads((agent / 'trajectory.json').read_text(encoding='utf-8'))['messages']
            index = record.get('delivered_message_index')
            after_text, after_program = None, None
            for m in messages[(index or 0) + 1:]:
                if m.get('role') != 'assistant':
                    continue
                if after_text is None:
                    after_text = m.get('content') or ''
                fence = FENCE.search(m.get('content') or '')
                heredoc = HEREDOC.search((m.get('content') or '')[fence.end():]) if fence else None
                if heredoc:
                    after_program = heredoc.group(2) + '\n'
                    break
            distinctive = {w.lower() for w in WORD.findall(message)} - {w.lower() for w in WORD.findall(statement)} - {
                'failure', 'observed', 'repair', 'direction', 'verification', 'target', 'program', 'public', 'output',
                'expected', 'printed', 'likely', 'should', 'instead', 'solution', 'workspace'}
            response_words = {w.lower() for w in WORD.findall(after_text or '')}
            program_lines = (after_program or '').split('\n')
            comment_words = {w.lower() for l in program_lines if l.strip().startswith('#') for w in WORD.findall(l)}
            code_words = {w.lower() for l in program_lines if l.strip() and not l.strip().startswith('#')
                          for w in WORD.findall(l)}
            sb, sa = (shape(before) if before else None), (shape(after_program) if after_program else None)
            changed = None
            if before is not None and after_program is not None:
                matcher = difflib.SequenceMatcher(None, before.split('\n'), after_program.split('\n'))
                changed = round(1 - matcher.ratio(), 3)
            evaluation = run_dir.parent / 'eval'
            hidden = None
            result = json.loads((run_dir / 'result.json').read_text(encoding='utf-8'))
            if (evaluation / f"{result['run_id']}.json").exists():
                hidden = json.loads((evaluation / f"{result['run_id']}.json").read_text(encoding='utf-8')).get('status')
            rows.append({
                'run': f'{study.name}/{run_dir.parent.name}/{run_dir.name}', 'task_id': packet['task_id'],
                'provider': record.get('provider'), 'seed': result.get('seed'), 'message_words': len(message.split()),
                'wrote_program_after': after_program is not None, 'changed_line_ratio': changed,
                'ast_identical': (sb or {}).get('dump_sha') == (sa or {}).get('dump_sha') if sb and sa else None,
                'loops_before_after': [(sb or {}).get('loops'), (sa or {}).get('loops')],
                'functions_before_after': [(sb or {}).get('functions'), (sa or {}).get('functions')],
                'imports_added': sorted(set((sa or {}).get('imports', [])) - set((sb or {}).get('imports', []))),
                'distinctive_message_words': len(distinctive),
                'uptake_response': round(len(distinctive & response_words) / len(distinctive), 3) if distinctive else None,
                'uptake_comments': round(len(distinctive & comment_words) / len(distinctive), 3) if distinctive else None,
                'uptake_code': round(len(distinctive & code_words) / len(distinctive), 3) if distinctive else None,
                'public_pass_after': (result.get('diagnosis') or {}).get('public_pass_after'), 'hidden_status': hidden})
    Path(out).write_text(json.dumps(rows, indent=1) + '\n', encoding='utf-8', newline='\n')
    for r in rows:
        print(json.dumps({k: r[k] for k in ('run', 'provider', 'changed_line_ratio', 'ast_identical', 'loops_before_after',
                                             'imports_added', 'uptake_comments', 'uptake_code', 'public_pass_after',
                                             'hidden_status')}))


if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:])
