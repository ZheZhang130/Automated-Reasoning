"""Export the official `final-main` study into this directory (read-only on the study root).

    python results/final-main/export_results.py E:\\CSC2108Local\\final-study

What is copied (paths relative to the study root -> this directory):

    report/{report.md,report.json,runs.csv,tasks.csv}           -> report/
    plans/final-main{,.freeze}.json                              -> study/plans/
    api-ledger.json, tasks-manifest.json, budget/ready records   -> study/
    OVERNIGHT_HANDOFF.md, PROGRESS.log, ops-logs/*               -> study/ops/
    guidance/**                                                  -> guidance/
    runs/final-main/{plan.json,provenance*.json*,measurements.jsonl} -> batch/
    runs/final-main/eval/*.json (hidden verdicts: counts/hashes) -> batch/eval/
    runs/final-main/<run>/{result.json,measurement.json,submission.py,attempts.jsonl} -> batch/runs/<run>/
    set-aside/final-main/{SET_ASIDE_LOG.jsonl,<run>/...}         -> set-aside/

Never copied: judge/ (public and hidden test suites), bundles/ (agent task bundles), the per-attempt agent
directories (trajectories, Ollama request/response/server logs: ~190 MB), per-attempt stdout logs, credentials.

Every file is scanned with guided_agent.privacy. A clean file is copied byte for byte. A file that names the local
user, host or home directory is passed through privacy.sanitize_text (fixed placeholders such as <USER>), re-scanned,
and marked "sanitized" in MANIFEST.json (its original sha256 is kept). Hidden-test content is refused: hidden
verdicts may only carry counts and hashes, and attempts.jsonl may only hold public-suite results.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[1]
sys.path.insert(0, str(REPO))
from guided_agent import privacy  # noqa: E402

BATCH = 'final-main'
RUN_FILES = ('result.json', 'measurement.json', 'submission.py', 'attempts.jsonl')
TEXT = {'.json', '.jsonl', '.md', '.csv', '.log', '.py', '.txt'}
HIDDEN_KEYS = ('cases', 'first_failure', 'input', 'expected', 'actual', 'stdin', 'stdout')


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def plan_files(study):
    pairs = [(study / 'report' / n, Path('report') / n) for n in ('report.md', 'report.json', 'runs.csv', 'tasks.csv')]
    pairs += [(study / 'plans' / n, Path('study/plans') / n) for n in (f'{BATCH}.json', f'{BATCH}.freeze.json')]
    for n in ('api-ledger.json', 'tasks-manifest.json', 'budget-preflight-initial.json', 'guidance-dryrun.json',
              'ready-pre-guidance.json', 'ready-final.json'):
        pairs.append((study / n, Path('study') / n))
    for n in ('OVERNIGHT_HANDOFF.md', 'PROGRESS.log'):
        pairs.append((study / n, Path('study/ops') / n))
    pairs += [(p, Path('study/ops/logs') / p.name) for p in sorted((study / 'ops-logs').iterdir())
              if p.is_file() and p.stat().st_size > 0]
    pairs += [(p, Path('guidance') / p.relative_to(study / 'guidance')) for p in sorted((study / 'guidance').rglob('*'))
              if p.is_file()]
    batch = study / 'runs' / BATCH
    for n in ('plan.json', 'provenance.json', 'provenance-sessions.jsonl', 'measurements.jsonl'):
        pairs.append((batch / n, Path('batch') / n))
    pairs += [(p, Path('batch/eval') / p.name) for p in sorted((batch / 'eval').glob('*.json'))]
    for run in sorted(d for d in batch.iterdir() if d.is_dir() and d.name.startswith('lcb-') and '.incomplete-' not in d.name):
        pairs += [(run / n, Path('batch/runs') / run.name / n) for n in RUN_FILES if (run / n).is_file()]
    aside = study / 'set-aside' / BATCH
    if aside.is_dir():
        pairs.append((aside / 'SET_ASIDE_LOG.jsonl', Path('set-aside/SET_ASIDE_LOG.jsonl')))
        for run in sorted(d for d in aside.iterdir() if d.is_dir()):
            pairs += [(run / n, Path('set-aside') / run.name / n) for n in RUN_FILES if (run / n).is_file()]
    return pairs


def guard_hidden(rel, text):
    """Refuse anything that could carry hidden-test contents."""
    if 'private_test_cases' in text:
        raise ValueError(f'{rel}: mentions private_test_cases')
    if rel.parts[:2] == ('batch', 'eval'):
        verdict = json.loads(text)
        if verdict.get('suite') != 'hidden' or any(k in verdict for k in HIDDEN_KEYS):
            raise ValueError(f'{rel}: hidden verdict with test-level content')
    if rel.name == 'attempts.jsonl':
        for line in text.splitlines():
            if line.strip() and (json.loads(line).get('result') or {}).get('suite') not in ('public', None):
                raise ValueError(f'{rel}: non-public suite in public-test attempts')


def main(study):
    study = Path(study).resolve()
    identity = privacy._identity()
    entries = []
    for src, rel in plan_files(study):
        data = src.read_bytes()
        dst = OUT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        entry = {'path': rel.as_posix(), 'source': src.relative_to(study).as_posix(), 'bytes': len(data),
                 'source_sha256': sha256(data), 'sanitized': False}
        if src.suffix in TEXT:
            text = data.decode('utf-8-sig', errors='strict')
            guard_hidden(rel, text)
            findings = privacy.scan(text, identity)
            if findings:
                clean = privacy.sanitize_text(text, identity)
                if privacy.scan(clean, identity):
                    raise ValueError(f'{rel}: still leaks after sanitizing')
                if src.suffix == '.json':
                    json.loads(clean)
                bom = data.startswith(b'\xef\xbb\xbf')
                out = (b'\xef\xbb\xbf' if bom else b'') + clean.encode('utf-8')
                dst.write_bytes(out)
                entry.update(sanitized=True, replaced=sorted({kind for kind, _ in findings}), bytes=len(out))
                data = out
            else:
                shutil.copyfile(src, dst)
        else:
            shutil.copyfile(src, dst)
        entry['sha256'] = sha256(data)
        entries.append(entry)
    manifest = {'schema': 'csc2108-results-export-v1', 'batch': BATCH, 'files': len(entries),
                'sanitized_files': sum(e['sanitized'] for e in entries),
                'bytes': sum(e['bytes'] for e in entries), 'entries': entries}
    (OUT / 'MANIFEST.json').write_text(json.dumps(manifest, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: v for k, v in manifest.items() if k != 'entries'}))


if __name__ == '__main__':
    main(sys.argv[1])
