"""Export sanitized summaries, manifests, and API ledger from study root into results/enhanced-de-v2/.

Uses `guided_agent.privacy.copy_sanitized_json` and `privacy.scan` so zero hostnames,
usernames, home directories, credentials, or hidden test contents ever enter Git.
"""

import argparse
from pathlib import Path

from guided_agent import privacy
from guided_agent.common import REPO, sha256_file, utc_now, write_json


DEFAULT_STUDY = Path(r'E:\CSC2108Local\enhanced-de-v2-study')
DEFAULT_OUT = REPO / 'results' / 'enhanced-de-v2'


def export_all(study=DEFAULT_STUDY, out_dir=DEFAULT_OUT):
    study = Path(study)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    exported = []

    # 1. Phase 0 / Phase 3 offline reports
    for src in sorted((study / 'reports').glob('*.json')):
        dst = out_dir / 'reports' / src.name
        privacy.copy_sanitized_json(src, dst)
        exported.append(dst)

    # 2. Live batch summaries (never raw hidden tests or agent logs)
    runs_dir = study / 'runs'
    if runs_dir.exists():
        for bdir in sorted(runs_dir.iterdir()):
            sum_path = bdir / 'summary.json'
            if sum_path.is_file():
                dst = out_dir / 'batches' / f'{bdir.name}.summary.json'
                privacy.copy_sanitized_json(sum_path, dst)
                exported.append(dst)

    # 2b. Authored artifacts and plans needed to reproduce the arms (statement-derived only; no hidden data):
    #     D2 bundles (contract + verification module, not the 91 MB of materialized stress inputs), the Codex
    #     plan-v1 artifacts for test5, the guided_agent plans, and each delivered E2 diagnosis (packet, response,
    #     delivered message, controller record).  Trajectories and Ollama logs stay in the study root.
    for src in sorted((study / 'd2_bundles').glob('*/*.bundle.json')):
        dst = out_dir / 'd2_bundles' / src.parent.name / src.name
        privacy.copy_sanitized_json(src, dst)
        exported.append(dst)
    for src in sorted((study / 'guidance').glob('*/*.json')):
        dst = out_dir / 'guidance' / src.parent.name / src.name
        privacy.copy_sanitized_json(src, dst)
        exported.append(dst)
    for src in sorted((study / 'plans').glob('*.json')):
        dst = out_dir / 'plans' / src.name
        privacy.copy_sanitized_json(src, dst)
        exported.append(dst)
    if runs_dir.exists():
        for src in sorted(runs_dir.glob('*/*/e2_diagnosis/diagnosis.json')):
            if '.incomplete-' in str(src) or '_archive' in str(src):
                continue
            dst = out_dir / 'diagnoses' / src.parents[2].name / f'{src.parents[1].name}.diagnosis.json'
            privacy.copy_sanitized_json(src, dst)
            exported.append(dst)

    # 3. API ledger
    ledger_src = study / 'api-ledger.json'
    if ledger_src.is_file():
        dst = out_dir / 'api-ledger.sanitized.json'
        privacy.copy_sanitized_json(ledger_src, dst)
        exported.append(dst)

    # 4. Scan ALL exported files + enhanced_de/docs/ for privacy leaks
    leaks = []
    for f in exported + sorted((REPO / 'enhanced_de' / 'docs').glob('*.md')):
        hits = privacy.scan(f.read_text(encoding='utf-8'))
        if hits:
            leaks.append({'file': str(f), 'hits': hits[:5]})
    if leaks:
        raise RuntimeError(f'Privacy scan failed on {len(leaks)} file(s): {leaks[:3]}')

    manifest = {
        'schema': 'csc2108-enhanced-de-export-manifest-v1',
        'exported_utc': utc_now(),
        'privacy_scan_passed': True,
        'files': [
            {
                'rel_path': str(p.relative_to(REPO)).replace('\\', '/'),
                'sha256': sha256_file(p),
                'bytes': p.stat().st_size,
            }
            for p in sorted(exported)
        ],
    }
    write_json(out_dir / 'MANIFEST.json', manifest)
    return manifest


def main():
    p = argparse.ArgumentParser(description='Export sanitized enhanced_de results to results/enhanced-de-v2/')
    p.add_argument('--study', default=str(DEFAULT_STUDY))
    p.add_argument('--out', default=str(DEFAULT_OUT))
    args = p.parse_args()
    m = export_all(args.study, args.out)
    print(f"Exported {len(m['files'])} sanitized files to {args.out} (privacy_scan_passed=True)", flush=True)


if __name__ == '__main__':
    main()
