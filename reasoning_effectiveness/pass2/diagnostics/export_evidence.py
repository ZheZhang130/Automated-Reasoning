"""Copy lightweight, sanitized pass-2 evidence into the repository (no programs, tests, packets or trajectories).

Kept: selection, freeze manifest, API ledger (no credentials ever stored), guidance artifacts (statement-derived
frontier text + provenance), batch plans, generated tables and per-run metric rows, contract-check counts, and
for each E run the delivered diagnosis TEXT with its hashes and outcome record. Excluded: candidate programs,
evidence packets (they embed the failed program), hidden tests, trajectories, Codex event logs.

usage: python -I export_evidence.py <pass2_study> <repo>/reasoning_effectiveness/pass2/evidence
"""
import json
import shutil
import sys
from pathlib import Path

study, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
for name in ('selection-pass2.json', 'FREEZE-val.json', 'api-ledger.json', 'analysis-contract-checks.json',
             'analysis-kcheck-programs.json'):
    if (study / name).exists():
        shutil.copyfile(study / name, out / name)
for name in ('pass2-tables.md', 'pass2-rows.json'):
    if (study / 'analysis' / name).exists():
        shutil.copyfile(study / 'analysis' / name, out / name)
(out / 'plans').mkdir(exist_ok=True)
for plan in sorted((study / 'plans').glob('*.json')):
    shutil.copyfile(plan, out / 'plans' / plan.name)
for artifact in sorted(study.glob('guidance/*/*.json')):
    if artifact.name.endswith('.response.json'):
        continue
    target = out / 'guidance' / artifact.parent.name / artifact.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(artifact, target)
diagnoses = []
for record_path in sorted(study.glob('runs/*/*/diagnosis/diagnosis.json')):
    record = json.loads(record_path.read_text(encoding='utf-8'))
    packet = record.get('packet') or {}
    response = record.get('response') or {}
    diagnoses.append({
        'run': f'{record_path.parts[-4]}/{record_path.parts[-3]}',
        'task_id': packet.get('task_id'), 'provider': (record.get('record') or {}).get('provider'),
        'candidate_sha256': packet.get('candidate_sha256'), 'report_sha256': packet.get('report_sha256'),
        'statement_sha256': packet.get('statement_sha256'), 'verdict': packet.get('verdict'),
        'diagnosis_text': response.get('text'),
        'model': response.get('model'), 'usage': response.get('usage'), 'cost_usd': response.get('cost_usd'),
        'latency_seconds': response.get('latency_seconds'), 'harness_wall_seconds': response.get('harness_wall_seconds'),
        'tool_events': ((response.get('isolation') or {}).get('tool_events')),
        'record': {k: v for k, v in (record.get('record') or {}).items() if k not in ('packet', 'response')},
    })
(out / 'diagnoses.json').write_text(json.dumps(diagnoses, indent=2, ensure_ascii=False) + '\n', encoding='utf-8',
                                    newline='\n')
print(len(diagnoses), 'diagnoses;', len(list((out / 'guidance').rglob('*.json'))), 'guidance artifacts')
