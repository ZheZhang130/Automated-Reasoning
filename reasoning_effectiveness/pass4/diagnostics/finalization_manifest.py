"""Write FINALIZATION_MANIFEST.json for the final branch (run from the repository root of that branch).

usage: python reasoning_effectiveness/pass4/diagnostics/finalization_manifest.py OUT.json SELECTION.json TESTS.json

SELECTION.json: {"development_commit": ..., "code_commit": ..., "agent": ..., "conditions": {...}, "open_decisions": [...]}
TESTS.json:     {"<suite>": {"command": ..., "ran": int, "skipped": int, "failures": int, "errors": int, "host": ...}, ...}

Hashes are sha256 of the file bytes (prompts: of the exact text the code sends). The manifest test
(guided_agent.test_final) recomputes the source and prompt hashes on every run.
"""
import hashlib
import importlib.metadata
import json
import platform
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(out, selection_path, tests_path):
    from guided_agent import agent_config, guidance
    from guided_agent.common import LCB_REVISION, MODEL, PROFILE
    selection = json.loads(Path(selection_path).read_text(encoding='utf-8'))
    tests = json.loads(Path(tests_path).read_text(encoding='utf-8'))
    frozen = json.loads((ROOT / 'local_optimization/final_selection.json').read_text(encoding='utf-8'))
    prompts = {pid: hashlib.sha256(text.encode('utf-8')).hexdigest() for pid, (_, text) in guidance.PROMPTS.items()}
    templates = {f'{iid}/{kind}': hashlib.sha256(text.encode('utf-8')).hexdigest()
                 for iid, group in guidance.INJECTION.items() for kind, text in group.items() if text}
    deliveries = {k: hashlib.sha256(v.encode('utf-8')).hexdigest() for k, v in guidance.DIAGNOSIS_DELIVERY.items()}
    sources = {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in sorted((ROOT / 'guided_agent').glob('*.py'))}
    agents = {k: agent_config.resolve(k)[2] for k in agent_config.AGENT_CONFIGS}
    manifest = {
        'schema': 'csc2108-finalization-manifest-v1',
        'branch': 'feat/csc2108-final-agent',
        'development_branch': 'feat/csc2108-contract-diagnosis-pass2',
        'development_commit': selection['development_commit'],
        'final_code_commit': selection['code_commit'],
        'selected': {'shared_agent': selection['agent'], 'shared_agent_definition_sha256': agents[selection['agent']],
                     'conditions': selection['conditions']},
        'agent_configurations': agents,
        'frozen_agent': {'model': MODEL, 'model_digest': frozen['model_digest'], 'profile': PROFILE,
                         'profile_config': frozen['frozen_configurations'][PROFILE],
                         'frozen_files': len(frozen['runtime_sha256']),
                         'selection_sha256': sha(ROOT / 'local_optimization/final_selection.json')},
        'prompt_sha256': prompts, 'injection_template_sha256': templates, 'diagnosis_delivery_sha256': deliveries,
        'source_sha256': sources,
        'dependencies': {p: importlib.metadata.version(p) for p in ('mini-swe-agent', 'litellm', 'pydantic', 'requests')},
        'python': platform.python_version(),
        'judge_version': '0.2.1', 'dataset_revision': LCB_REVISION,
        'tests': tests,
        'compatibility': selection.get('compatibility', {}),
        'open_decisions': selection.get('open_decisions', []),
    }
    Path(out).write_text(json.dumps(manifest, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: manifest[k] for k in ('development_commit', 'final_code_commit', 'selected')}, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:])
