"""Export sanitized run fixtures for the evaluation pipeline (Peter's ingestion tests), without any model call.

usage: python reasoning_effectiveness/pass4/diagnostics/export_fixtures.py FIXTURE_DIR ROLE=RUN_DIR [ROLE=RUN_DIR ...]

For each role, copies only machine-readable records: ``result.json``, ``measurement.json`` (rebuilt from the
original run directory), ``attempts.jsonl`` and the hidden ``eval.json`` if present. Sanitization:

* user names, home directories, host names and secrets are replaced by placeholders (``guided_agent.privacy``);
* judge-public report text and diagnosis/coder texts are replaced by their sha256 (no test data, no model text);
* candidate programs, trajectories, statements, raw requests/responses and hidden tests are never copied.

Every written file is scanned again; the export fails if anything identifying remains.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from guided_agent import measurement, privacy  # noqa: E402
from guided_agent.common import read_json, sha256_text, write_json  # noqa: E402

TEXT_KEYS = {'report', 'output', 'text', 'diagnosis_text', 'delivered_message', 'user_message', 'error_text'}


def strip(value):
    if isinstance(value, dict):
        return {k: (('sha256:' + sha256_text(v)) if k in TEXT_KEYS and isinstance(v, str) and len(v) > 80 else strip(v))
                for k, v in value.items()}
    if isinstance(value, list):
        return [strip(v) for v in value]
    return value


def export(fixtures, role, run_dir):
    run_dir = Path(run_dir)
    out = Path(fixtures) / role
    out.mkdir(parents=True, exist_ok=True)
    record = read_json(run_dir / 'result.json')
    files = {'result.json': strip(record), 'measurement.json': measurement.build(run_dir)}
    hidden = run_dir.parent / 'eval' / f"{record['run_id']}.json"
    if hidden.exists():
        files['eval.json'] = read_json(hidden)
    for name, value in files.items():
        write_json(out / name, privacy.sanitize(value))
    attempts = run_dir / 'attempts.jsonl'
    if attempts.exists():
        lines = [json.dumps(privacy.sanitize(strip(json.loads(line))), ensure_ascii=False)
                 for line in attempts.read_text(encoding='utf-8').splitlines() if line.strip()]
        (out / 'attempts.jsonl').write_text(''.join(l + '\n' for l in lines), encoding='utf-8', newline='\n')
    for path in out.iterdir():
        findings = privacy.scan(path.read_text(encoding='utf-8'))
        if findings:
            raise SystemExit(f'{path}: identifying content remains: {findings[:3]}')
    problems = measurement.conforms(files['measurement.json'])
    if problems:
        raise SystemExit(f'{role}: measurement does not conform: {problems[:3]}')
    return {'role': role, 'run_id': record['run_id'], 'condition': record['condition'],
            'exit_status': record.get('exit_status'), 'hidden': files.get('eval.json', {}).get('status')}


def main(fixtures, *pairs):
    index = [export(fixtures, *pair.split('=', 1)) for pair in pairs]
    write_json(Path(fixtures) / 'INDEX.json', privacy.sanitize(index))
    for entry in index:
        print(json.dumps(entry))


if __name__ == '__main__':
    main(*sys.argv[1:])
