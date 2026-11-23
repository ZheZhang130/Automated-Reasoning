"""D-active development analysis: are the contract K-checks' proposed outputs correct, and do they catch wrong programs?

usage: python reasoning_effectiveness/pass4/diagnostics/check_validity.py OUT.json GUIDANCE_DIR STUDY_ROOT [STUDY_ROOT ...]

Endres-style metrics (pass-2 `contract_checks.py`, reused): a check is CORRECT if a reference program (a submission
that passed all hidden cases) prints its proposed output; a correct check CATCHES a natural wrong program (a failed
submission of the same task) if that program's output differs or it errors. Every program runs in a network-less,
read-only, unprivileged container, never on the host. This analysis is never shown to any model and never used to
build model-facing checks. Only counts and check IDs are written.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'reasoning_effectiveness/pass2/diagnostics'))
from contract_checks import run_program  # noqa: E402  (pass-2 sandbox runner)
from guided_agent import contract_checks  # noqa: E402
from guided_agent.checkers import outputs_match  # noqa: E402


def submissions(studies, task_id):
    pool = {}
    for study in studies:
        for result in Path(study).glob('runs/*/*/result.json'):
            try:
                record = json.loads(result.read_text(encoding='utf-8'))
            except ValueError:
                continue
            if record.get('task_id') != task_id or not (result.parent / 'submission.py').exists():
                continue
            hidden = result.parent.parent / 'eval' / f"{record['run_id']}.json"
            if not hidden.exists():
                continue
            status = json.loads(hidden.read_text(encoding='utf-8')).get('status')
            pool.setdefault(record.get('submission_sha256'), {'code': (result.parent / 'submission.py').read_bytes(),
                                                              'status': status})
    return pool


def main(out, guidance_dir, *studies):
    report = []
    for path in sorted(Path(guidance_dir).glob('*.contract-v3.*.json')):
        raw = json.loads(path.read_text(encoding='utf-8'))
        task_id = raw['task_id']
        public = json.loads((Path(studies[0]) / 'bundles' / task_id / 'public_tests.json').read_text(encoding='utf-8'))
        accepted, labels = contract_checks.validate(contract_checks.parse_checks(raw['text']), public)
        pool = submissions(studies, task_id)
        references = [p for p in pool.values() if p['status'] == 'pass']
        wrong = [p for p in pool.values() if p['status'] == 'candidate_failure']
        entry = {'task_id': task_id, 'artifact_sha256': __import__('hashlib').sha256(path.read_bytes()).hexdigest(),
                 'checks_accepted': len(accepted), 'labels': [l['status'] for l in labels],
                 'references': len(references), 'wrong_programs': len(wrong)}
        if accepted and references:
            inputs = [c['stdin'] for c in accepted]
            outputs = run_program(references[0]['code'], inputs)
            correct = [o['rc'] == 0 and outputs_match(o['stdout'], c['expected']) for o, c in zip(outputs, accepted)]
            entry['correct'] = sum(correct)
            entry['incorrect_ids'] = [c['id'] for c, ok in zip(accepted, correct) if not ok]
            caught = 0
            for program in wrong:
                results = run_program(program['code'], inputs)
                caught += any(ok and (r['rc'] != 0 or not outputs_match(r['stdout'], c['expected']))
                              for r, c, ok in zip(results, accepted, correct))
            entry['wrong_programs_caught'] = caught
        report.append(entry)
        print(json.dumps(entry), flush=True)
    Path(out).write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main(*sys.argv[1:])
