"""Freeze the pass-3 extended benchmark in two stages (run from the repository root).

  stage 1 (before any guidance or run):  python -m reasoning_effectiveness.pass3.diagnostics.write_freeze config <study>
  stage 2 (after guidance, before runs): python -m reasoning_effectiveness.pass3.diagnostics.write_freeze guidance <study>

Stage 1 writes FREEZE-ext.json (selection, configuration, prompts, policies, evaluation commands, analysis
plan) and the two batch plans. Stage 2 adds FREEZE-ext-guidance.json with every C/D artifact hash. Neither
stage reads any model outcome.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from guided_agent import guidance
from guided_agent.common import ACTIONS, MODEL, PROFILE, REPAIRS, REPO, SECONDS, read_json, sha256_file, utc_now, write_json
from guided_agent.integrity import validate_plan

SEEDS = (2108, 2109)
DIAGNOSIS = {'provider': 'codex', 'timeout': 300, 'prompt_id': 'diagnosis-v1', 'delivery': 'deliver-v1'}
LABEL = 'ext-codex'


def sha_text(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def git(*args):
    return subprocess.run(['git', *args], cwd=REPO, capture_output=True, text=True).stdout.strip()


def guidance_path(study, task, prompt_id):
    return str(Path(study) / 'guidance' / LABEL / f'{task}.{prompt_id}.codex.json')


def plan_for(study, tasks, seed):
    attempts = []
    for task in tasks:  # interleaved by task: an early stop still leaves complete matched blocks
        attempts += [{'task_id': task, 'condition': 'A', 'seed': seed},
                     {'task_id': task, 'condition': 'C', 'seed': seed, 'guidance': guidance_path(study, task, 'plan-v1')},
                     {'task_id': task, 'condition': 'D', 'seed': seed,
                      'guidance': guidance_path(study, task, 'contract-v1')},
                     {'task_id': task, 'condition': 'E', 'seed': seed, 'diagnosis': dict(DIAGNOSIS)}]
    return {'batch': f'ext-s{seed}', 'cohort': 'pass-3 extended benchmark (fresh, outcome-blind, hard-heavy)',
            'frozen': True, 'outer_timeout': 960, 'max_resource_wait': 1800, 'attempts': attempts}


def stage_config(study):
    selection = read_json(study / 'selection-pass3.json')
    tasks = [t['task_id'] for t in selection['frozen_order']]
    manifest = read_json(study / 'tasks-manifest.json')
    freeze = {
        'created_utc': utc_now(), 'stage': 'config (before any guidance generation or local run)',
        'cohort': 'pass-3 extended benchmark: 12 fresh AtCoder tasks, all labelled hard by LiveCodeBench '
                  '(hard-heavy by necessity; ordered by public contest letter band)',
        'source_commit': git('rev-parse', 'HEAD'), 'source_dirty': bool(git('status', '--porcelain', '--', 'guided_agent',
                                                                            'local_eval_v2', 'local_baseline', 'judge')),
        'guided_agent_sha256': {p.name: sha256_file(p) for p in sorted((REPO / 'guided_agent').glob('*.py'))},
        'dataset': {'name': 'livecodebench/code_generation_lite', 'revision': manifest['hf_revision'],
                    'shard': 'test6.jsonl', 'shard_sha256': manifest['shard_sha256'],
                    'note': 'newest official revision and shard on 2026-11-22 (HF API); no newer shard exists'},
        'selection': {'file_sha256': sha256_file(study / 'selection-pass3.json'), 'rule': selection['rule'],
                      'pool_by_band': selection['pool_by_band'],
                      'excluded_output_semantics': [(e['task_id'], e['output_category'])
                                                    for e in selection['excluded_output_semantics']],
                      'review_sha256': selection['review_sha256']},
        'tasks': [{'task_id': t, 'order': i + 1, 'band': selection['frozen_order'][i]['band'],
                   'difficulty': manifest['tasks'][t]['difficulty'], 'n_public': manifest['tasks'][t]['n_public'],
                   'n_hidden': manifest['tasks'][t]['n_hidden'], 'statement_sha256': manifest['tasks'][t]['statement_sha256'],
                   'public_sha256': manifest['tasks'][t]['public_sha256'], 'hidden_sha256': manifest['tasks'][t]['hidden_sha256']}
                  for i, t in enumerate(tasks)],
        'judge': {'version': 'csc2108-judge:0.2.1', 'output_rule': 'exact (LiveCodeBench grade_stdio); every task '
                  'reviewed as single-answer exact output', 'public': 'judge-public (public tests only)',
                  'hidden': 'judge-hidden, separate container, after all attempts of a batch'},
        'agent': {'model': MODEL, 'digest': '56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90',
                  'quantization': 'Q4_K_M', 'backend': 'mini-swe-agent 2.4.6 frozen local_eval_v2.runtime.run (38 hashes)',
                  'profile': PROFILE, 'budgets': {'actions': ACTIONS, 'repair_groups': REPAIRS, 'seconds': SECONDS,
                                                  'request_seconds': 180}, 'aci': 'none (original frozen agent)'},
        'conditions': {'A': 'local only', 'C': 'plan-v1 + inject-v1', 'D': 'contract-v1 + inject-v1',
                       'E': 'diagnosis-v1 + deliver-v1, first qualifying public failure, one live call, same session'},
        'seeds': list(SEEDS),
        'prompts_sha256': {k: sha_text(guidance.PROMPTS[k][1]) for k in ('plan-v1', 'contract-v1', 'diagnosis-v1')},
        'injection_sha256': {'inject-v1': sha_text(json.dumps(guidance.INJECTION['inject-v1'], sort_keys=True))},
        'delivery_sha256': {'deliver-v1': sha_text(guidance.DIAGNOSIS_DELIVERY['deliver-v1'])},
        'frontier_provider': {'C/D guidance': 'Codex-authored (isolated codex exec, gpt-6.2-sol, effort medium), '
                                              'statement + versioned system prompt only, once per task, reused '
                                              'for both seeds', 'E diagnosis': dict(DIAGNOSIS),
                              'paid API': 'not used in this cohort'},
        'policies': {
            'guidance_generation': 'One Codex call per task and kind. A provider failure (timeout, transport, '
                                   'isolation violation, empty) may be retried once, labelled; a format-invalid '
                                   'artifact is final and its runs count as failures of that condition (intention '
                                   'to treat). No artifact is ever regenerated because of its content.',
            'execution': 'Seed 2108 matrix first, then seed 2109; sequential under the project GPU lock; tasks in '
                         'frozen order with A, C, D, E interleaved per task; checkpoint after every attempt.',
            'second_seed_reduction': 'If the full seed-2109 matrix cannot finish, keep the longest prefix of the '
                                     'frozen task order with all four conditions complete; report it as such.',
            'infrastructure': 'An attempt ending in infra_error or setup_error is recorded and never rerun; its '
                              '(task, seed) block is excluded from paired comparisons for every condition and '
                              'reported. A resource deferral (foreign models) consumes no attempt.',
            'e_provider_failures': 'Part of the E outcome; no retry.',
            'scoring': 'Hidden judge after each batch; missing submission = failure.',
            'no_tuning': 'No prompt, runtime or selection change after this freeze; findings go to future work.'},
        'analysis_plan': ['per-condition hidden accuracy per seed and pooled over seeds',
                          'paired gains/harms vs A per (task, seed); C vs D, C vs E, D vs E',
                          'task-clustered bootstrap intervals for paired differences (tasks resampled, seeds kept)',
                          'E: trigger rate over all assigned runs, delivery, post-diagnosis change and recovery',
                          'tokens, local and end-to-end time, format errors and truncations, identical rewrites'],
        'evaluation_commands': ['python -m guided_agent batch <study>/plans/ext-s2108.json',
                                'python -m guided_agent evaluate <study>/runs/ext-s2108',
                                'python -m guided_agent batch <study>/plans/ext-s2109.json',
                                'python -m guided_agent evaluate <study>/runs/ext-s2109'],
    }
    plans = {}
    for seed in SEEDS:
        plan = plan_for(study, tasks, seed)
        problems = [p for p in validate_plan(plan) if 'does not exist' not in p]  # artifacts come in stage 2
        if problems:
            raise SystemExit(problems)
        write_json(study / 'plans' / f'ext-s{seed}.json', plan)
        plans[f'ext-s{seed}'] = sha256_file(study / 'plans' / f'ext-s{seed}.json')
    freeze['plans_sha256'] = plans
    write_json(study / 'FREEZE-ext.json', freeze)
    print(freeze['source_commit'], len(tasks), 'tasks;', plans)


def stage_guidance(study):
    freeze = read_json(study / 'FREEZE-ext.json')
    artifacts, problems = {}, []
    for task in [t['task_id'] for t in freeze['tasks']]:
        for prompt in ('plan-v1', 'contract-v1'):
            path = Path(guidance_path(study, task, prompt))
            record = read_json(path)
            artifacts[f'{task}:{prompt}'] = {'sha256': sha256_file(path), 'word_count': record.get('word_count'),
                                             'validation_problems': record.get('validation_problems'),
                                             'statement_sha256': record.get('statement_sha256'),
                                             'observed_model': record.get('observed_model'),
                                             'created_utc': record.get('created_utc')}
            if record.get('statement_sha256') != next(t['statement_sha256'] for t in freeze['tasks'] if t['task_id'] == task):
                problems.append(f'{task}:{prompt} statement hash mismatch')
    for seed in SEEDS:
        plan = read_json(study / 'plans' / f'ext-s{seed}.json')
        problems += validate_plan(plan)
        if sha256_file(study / 'plans' / f'ext-s{seed}.json') != freeze['plans_sha256'][f'ext-s{seed}']:
            problems.append(f'plan ext-s{seed} changed after stage 1')
    if problems:
        raise SystemExit(problems)
    out = {'created_utc': utc_now(), 'stage': 'guidance (before any local run)',
           'freeze_config_sha256': sha256_file(study / 'FREEZE-ext.json'), 'artifacts': artifacts,
           'source_commit': git('rev-parse', 'HEAD')}
    write_json(study / 'FREEZE-ext-guidance.json', out)
    print(len(artifacts), 'artifacts frozen')


if __name__ == '__main__':
    {'config': stage_config, 'guidance': stage_guidance}[sys.argv[1]](Path(sys.argv[2]))
