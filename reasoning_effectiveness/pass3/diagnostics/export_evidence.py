"""Copy lightweight, SANITIZED pass-3 evidence into the repository (run from the repository root).

  python -m reasoning_effectiveness.pass3.diagnostics.export_evidence <pass3_study> [part ...]

Parts: freeze (freeze manifests, selection, plans), guidance (C/D artifacts), ledger, runs (per-attempt public and
hidden outcome metadata as hashes and verdict counts), diagnoses (E texts with
hashes and outcome records), analysis (generated tables and per-run rows). Every JSON copy goes through
``guided_agent.privacy.copy_sanitized_json``, which refuses a copy that still contains a home path, user name,
host name or secret. Excluded always: candidate programs, evidence packets (they embed programs), hidden tests,
trajectories, raw model responses and Codex event logs. Private originals keep their recorded hashes.
"""
import json
import sys
from pathlib import Path

from guided_agent import privacy
from guided_agent.common import REPO, sha256_file

OUT = REPO / 'reasoning_effectiveness/pass3/evidence'


def export(study, parts):
    study = Path(study)
    done = {}
    if 'freeze' in parts:
        for name in ('FREEZE-ext.json', 'FREEZE-ext-guidance.json', 'selection-pass3.json'):
            if (study / name).exists():
                privacy.copy_sanitized_json(study / name, OUT / name)
        for plan in sorted((study / 'plans').glob('*.json')):
            privacy.copy_sanitized_json(plan, OUT / 'plans' / plan.name)
        done['freeze'] = True
    if 'guidance' in parts:
        n = 0
        for artifact in sorted(study.glob('guidance/*/*.json')):
            if artifact.name.endswith('.response.json'):
                continue
            privacy.copy_sanitized_json(artifact, OUT / 'guidance' / artifact.parent.name / artifact.name)
            n += 1
        done['guidance'] = n
    if 'ledger' in parts and (study / 'api-ledger.json').exists():
        privacy.copy_sanitized_json(study / 'api-ledger.json', OUT / 'api-ledger.json')
        done['ledger'] = True
    if 'diagnoses' in parts:
        rows = []
        for path in sorted(study.glob('runs/*/*/diagnosis/diagnosis.json')):
            record = json.loads(path.read_text(encoding='utf-8'))
            packet, response = record.get('packet') or {}, record.get('response') or {}
            rows.append({'run': f'{path.parts[-4]}/{path.parts[-3]}', 'task_id': packet.get('task_id'),
                         'provider': (record.get('record') or {}).get('provider'),
                         'candidate_sha256': packet.get('candidate_sha256'), 'report_sha256': packet.get('report_sha256'),
                         'statement_sha256': packet.get('statement_sha256'), 'verdict': packet.get('verdict'),
                         'diagnosis_text': response.get('text'), 'model': response.get('model'),
                         'usage': response.get('usage'), 'cost_usd': response.get('cost_usd'),
                         'latency_seconds': response.get('latency_seconds'),
                         'harness_wall_seconds': response.get('harness_wall_seconds'),
                         'tool_events': (response.get('isolation') or {}).get('tool_events'),
                         'record': {k: v for k, v in (record.get('record') or {}).items()
                                    if k not in ('packet', 'response')}})
        tmp = study / 'analysis' / 'diagnoses-export.json'
        tmp.parent.mkdir(exist_ok=True)
        tmp.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
        privacy.copy_sanitized_json(tmp, OUT / 'diagnoses.json')
        done['diagnoses'] = len(rows)
    if 'runs' in parts:
        # per-attempt metadata: public attempts and hidden outcome as hashes and verdict counts (no code, no tests)
        rows = []
        for result in sorted(study.glob('runs/*/*/result.json')):
            run_dir, batch = result.parent, result.parent.parent.name
            if batch.startswith('integration') or 'incomplete' in run_dir.name:
                continue
            record = json.loads(result.read_text(encoding='utf-8'))
            public = []
            attempts = run_dir / 'attempts.jsonl'
            for line in (attempts.read_text(encoding='utf-8').splitlines() if attempts.exists() else []):
                item = json.loads(line)
                res = item.get('result') or {}
                public.append({'seq': item.get('seq'), 'action': item.get('action'), 'code_sha256': res.get('code_sha256'),
                               'status': res.get('status'), 'passed': res.get('passed'), 'total': res.get('total'),
                               'verdict_counts': res.get('verdict_counts'), 'tests_sha256': res.get('tests_sha256')})
            hidden = None
            for path in sorted((run_dir.parent / 'eval').glob(f"{record.get('run_id')}.json")):
                h = json.loads(path.read_text(encoding='utf-8'))
                hidden = {k: h.get(k) for k in ('status', 'passed', 'total', 'verdict_counts', 'code_sha256',
                                                'tests_sha256', 'judge_version', 'evaluated_utc')}
            rows.append({'batch': batch, 'run_id': record.get('run_id'), 'task_id': record.get('task_id'),
                         'condition': record.get('condition'), 'seed': record.get('seed'),
                         'exit_status': record.get('exit_status'), 'raw_exit_status': record.get('raw_exit_status'),
                         'n_actions': record.get('n_actions'), 'n_repairs': record.get('n_repairs'),
                         'wall_seconds': record.get('wall_seconds'), 'model_digest': record.get('model_digest'),
                         'frozen_files_verified': (record.get('frozen_verification') or {}).get('frozen_files_verified'),
                         'submission_sha256': sha256_file(run_dir / 'submission.py')
                         if (run_dir / 'submission.py').exists() else None,
                         'public_attempts': public, 'hidden': hidden})
        tmp = study / 'analysis' / 'runs-export.json'
        tmp.write_text(json.dumps(rows, indent=1) + '\n', encoding='utf-8', newline='\n')
        privacy.copy_sanitized_json(tmp, OUT / 'runs.json')
        tmp.unlink()
        done['runs'] = len(rows)
    if 'analysis' in parts:
        for path in sorted((study / 'analysis').glob('*')):
            if path.name == 'diagnoses-export.json' or path.stat().st_size > 3_000_000:
                continue
            if path.suffix == '.json':
                privacy.copy_sanitized_json(path, OUT / 'analysis' / path.name)
            elif path.suffix in ('.md', '.txt', '.csv'):
                text = privacy.sanitize_text(path.read_text(encoding='utf-8'))
                if privacy.scan(text):
                    raise ValueError(f'{path} still leaks after sanitizing')
                (OUT / 'analysis').mkdir(parents=True, exist_ok=True)
                (OUT / 'analysis' / path.name).write_text(text, encoding='utf-8', newline='\n')
        done['analysis'] = True
    print(json.dumps(done))


if __name__ == '__main__':
    export(sys.argv[1], set(sys.argv[2:]) or {'freeze', 'guidance', 'ledger', 'diagnoses', 'runs', 'analysis'})
