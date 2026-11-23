"""Stable per-attempt measurement record (schema ``csc2108-run-measurement-v1``) for the evaluation pipeline.

``build(run_dir)`` derives one JSON document from the artifacts an attempt already writes (``result.json``, the
frozen agent's ``result.json``/``trajectory.json``/``ollama-responses.json``, ``attempts.jsonl``, the guidance
artifact, coder and diagnosis logs) plus the hidden-evaluation file when it exists. It never re-runs anything.

Rules: units are in the field names (``_seconds``, ``_tokens``, ``_usd``, ``_chars``); a value that the source does not
report is ``null`` (never 0); every cost is labelled measured (API ledger) or absent (Codex replay); modelled
quantities (electricity) are only produced when the caller supplies the model parameters, and are labelled so.
``FIELDS`` is the single source of the documentation table (``python -m guided_agent schema``).
"""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from .common import LCB_REVISION, read_json, sha256_text, utc_now, write_json

SCHEMA = 'csc2108-run-measurement-v1'
WRITE = re.compile(r'(?:cat|tee)\s*>?\s*/workspace/solution\.py|>\s*/workspace/solution\.py|sed\s+-i\b.*solution\.py')
TEST = re.compile(r'^\s*python(?:3)?\s+(?:-I\s+)?/public/check\.py(?:\s*<\s*[^;&|\s]+)?\s*$')

# (field path, type, unit, nullable, source, kind, applies to)
# kind: measured | derived | configuration | identity | modelled
FIELDS = [
    ('schema', 'str', '', False, 'constant', 'identity', 'all'),
    ('identity.run_id', 'str', '', False, 'result.json', 'identity', 'all'),
    ('identity.task_id', 'str', '', False, 'result.json', 'identity', 'all'),
    ('identity.condition', 'str', 'A|B|C|D|E', False, 'result.json', 'identity', 'all'),
    ('identity.seed', 'int', '', False, 'result.json', 'configuration', 'all'),
    ('identity.batch', 'str', '', True, 'result.json', 'identity', 'all'),
    ('identity.agent_config_id', 'str', '', False, 'result.json agent_config', 'configuration', 'all'),
    ('identity.agent_config_sha256', 'str', 'sha256', True, 'agent_config definition', 'configuration', 'all'),
    ('identity.guidance_prompt_id', 'str', '', True, 'guidance artifact', 'configuration', 'C, D'),
    ('identity.injection', 'str', '', True, 'spec', 'configuration', 'C, D'),
    ('identity.diagnosis_prompt_id', 'str', '', True, 'spec', 'configuration', 'E'),
    ('identity.diagnosis_delivery', 'str', '', True, 'spec', 'configuration', 'E'),
    ('identity.source_commit', 'str', 'git sha', True, 'git rev-parse at run time', 'identity', 'all'),
    ('identity.source_dirty', 'bool', '', True, 'git status of agent paths', 'identity', 'all'),
    ('identity.coding_model', 'str', '', False, 'result.json', 'identity', 'all'),
    ('identity.coding_model_digest', 'str', 'sha256', True, 'Ollama /api/tags (local only)', 'measured', 'A, C, D, E'),
    ('identity.profile', 'str', '', False, 'result.json', 'configuration', 'all'),
    ('identity.profile_config', 'object', '', True, 'frozen record profile_config (overlay applied)', 'configuration', 'A, C, D, E'),
    ('identity.frontier_provider', 'str', 'openai-api|codex-replay|...', True, 'guidance/diagnosis/coder records', 'identity', 'B, C, D, E'),
    ('identity.frontier_requested_model', 'str', '', True, 'guidance/diagnosis/coder records', 'identity', 'B, C, D, E'),
    ('identity.frontier_observed_model', 'str', '', True, 'API response model field', 'measured', 'B, C, D, E (API)'),
    ('identity.dataset_revision', 'str', 'git sha', False, 'common.LCB_REVISION', 'identity', 'all'),
    ('identity.judge_version', 'str', '', True, 'judge-public info', 'identity', 'all'),
    ('identity.judge_public_tests_sha256', 'str', 'sha256', True, 'judge-public info', 'identity', 'all'),
    ('identity.guidance_artifact_sha256', 'str', 'sha256', True, 'artifact file', 'identity', 'C, D'),
    ('identity.frozen_files_verified', 'int', 'files', True, 'local_agent verify', 'measured', 'all'),
    ('identity.sampler_wire_verified', 'bool', '', True, 'captured Ollama requests', 'measured', 'A, C, D, E'),
    ('identity.host', 'object', '', False, 'platform', 'identity', 'all'),
    ('identity.host_backend', 'str', 'windows|portable', False, 'result.json', 'identity', 'all'),
    ('correctness.candidate_produced', 'bool', '', False, 'submission_sha256 present', 'measured', 'all'),
    ('correctness.submitted', 'bool', '', False, 'raw exit = Submitted', 'measured', 'all'),
    ('correctness.public_tests_invoked', 'int', 'count', False, 'attempts.jsonl', 'measured', 'all'),
    ('correctness.public_pass', 'bool', '', False, 'any public test passed', 'measured', 'all'),
    ('correctness.final_public_status', 'str', 'pass|candidate_failure|none', False, 'last public test', 'measured', 'all'),
    ('correctness.public_runtime_error_cases', 'int', 'cases', False, 'sum of RE verdicts over public tests', 'measured', 'all'),
    ('correctness.hidden_status', 'str', 'pass|candidate_failure|missing_submission|...', True, 'eval/<run_id>.json', 'measured', 'all'),
    ('correctness.hidden_passed', 'int', 'cases', True, 'eval/<run_id>.json', 'measured', 'all'),
    ('correctness.hidden_total', 'int', 'cases', True, 'eval/<run_id>.json', 'measured', 'all'),
    ('correctness.exit_status', 'str', 'submitted|action_limit|repair_limit|deadline|agent_error|infra_error', False, 'runner.exit_status', 'measured', 'all'),
    ('correctness.raw_exit_status', 'str', '', True, 'mini-SWE-agent exit', 'measured', 'all'),
    ('correctness.infrastructure_failure', 'bool', '', False, 'exit infra_error or setup error, excluding context_overflow', 'derived', 'all'),
    ('correctness.setup_error', 'str', '', True, 'result.json', 'measured', 'all'),
    ('correctness.context_overflow', 'bool', '', False, 'the model request failed (Ollama connection error) when the last prompt plus output was within 1,024 tokens of num_ctx: the agent exhausted its context; recorded by the runner as infra_error but deterministic, so not an infrastructure failure', 'derived', 'A, C, D, E'),
    ('local_inference.calls', 'int', 'requests', False, 'ollama-responses.json', 'measured', 'A, C, D, E (0 for B)'),
    ('local_inference.prompt_tokens', 'int', 'tokens', True, 'prompt_eval_count', 'measured', 'A, C, D, E'),
    ('local_inference.completion_tokens', 'int', 'tokens', True, 'eval_count (includes thinking)', 'measured', 'A, C, D, E'),
    ('local_inference.reasoning_tokens', 'int', 'tokens', True, 'not reported by Ollama: always null', 'measured', 'A, C, D, E'),
    ('local_inference.thinking_chars', 'int', 'characters', True, 'message.thinking', 'measured', 'A, C, D, E'),
    ('local_inference.max_prompt_tokens', 'int', 'tokens', True, 'max prompt_eval_count', 'measured', 'A, C, D, E'),
    ('local_inference.context_tokens_limit', 'int', 'tokens', True, 'profile num_ctx', 'configuration', 'A, C, D, E'),
    ('local_inference.output_tokens_limit', 'int', 'tokens', True, 'profile num_predict', 'configuration', 'A, C, D, E'),
    ('local_inference.prompt_eval_seconds', 'float', 's', True, 'prompt_eval_duration', 'measured', 'A, C, D, E'),
    ('local_inference.eval_seconds', 'float', 's', True, 'eval_duration', 'measured', 'A, C, D, E'),
    ('local_inference.load_seconds', 'float', 's', True, 'load_duration', 'measured', 'A, C, D, E'),
    ('local_inference.total_inference_seconds', 'float', 's', True, 'sum of total_duration', 'measured', 'A, C, D, E'),
    ('local_inference.truncated_responses', 'int', 'responses', False, "done_reason == 'length'", 'measured', 'all'),
    ('local_inference.format_errors', 'int', 'responses', False, 'trajectory FormatError messages', 'measured', 'all'),
    ('local_inference.self_plan', 'object', '', True, 'self-plan.json (agent l1 only)', 'measured', 'l1 configurations'),
    ('agent.actions', 'int', 'actions', False, 'Budget', 'measured', 'all'),
    ('agent.repairs', 'int', 'repair groups', False, 'Budget', 'measured', 'all'),
    ('agent.model_calls', 'int', 'requests', False, 'mini-SWE-agent n_calls', 'measured', 'all'),
    ('agent.source_writes', 'int', 'commands', False, 'commands writing solution.py', 'derived', 'all'),
    ('agent.distinct_sources', 'int', 'versions', False, 'distinct snapshot hashes', 'derived', 'all'),
    ('agent.unchanged_writes', 'int', 'commands', False, 'write left the snapshot unchanged', 'derived', 'all'),
    ('agent.rewrites_of_failed_candidate', 'int', 'commands', False, 'write produced a source that already failed public tests', 'derived', 'all'),
    ('agent.repeated_responses', 'int', 'responses', False, 'assistant message identical to the previous one', 'derived', 'all'),
    ('agent.public_test_attempts', 'int', 'count', False, 'attempts.jsonl', 'measured', 'all'),
    ('agent.seconds_to_first_valid_action', 'float', 's from first model request', True, 'Ollama created_at/total_duration', 'derived', 'A, C, D, E'),
    ('agent.seconds_to_first_executable_candidate', 'float', 's from first model request', True, 'first public test with an AC or WA case', 'derived', 'A, C, D, E'),
    ('agent.seconds_to_first_public_test', 'float', 's from first model request', True, 'Ollama timestamps', 'derived', 'A, C, D, E'),
    ('frontier.requests', 'list', '', False, 'see frontier.requests[] fields below', 'measured', 'all ([] for A)'),
    ('frontier.requests[].type', 'str', 'guidance|diagnosis|coder_turn', False, 'record', 'identity', 'B, C, D, E'),
    ('frontier.requests[].prompt_id', 'str', '', True, 'record', 'configuration', 'C, D, E'),
    ('frontier.requests[].provider', 'str', '', True, 'record', 'identity', 'B, C, D, E'),
    ('frontier.requests[].utc', 'str', 'ISO 8601 UTC', True, 'record', 'measured', 'B, C, D, E'),
    ('frontier.requests[].input_tokens', 'int', 'tokens', True, 'provider usage (Codex: includes its harness context)', 'measured', 'B, C, D, E'),
    ('frontier.requests[].output_tokens', 'int', 'tokens', True, 'provider usage', 'measured', 'B, C, D, E'),
    ('frontier.requests[].reasoning_tokens', 'int', 'tokens', True, 'provider usage', 'measured', 'B, C, D, E'),
    ('frontier.requests[].cached_input_tokens', 'int', 'tokens', True, 'provider usage', 'measured', 'B, C, D, E'),
    ('frontier.requests[].latency_seconds', 'float', 's', True, 'provider call wall time', 'measured', 'B, C, D, E'),
    ('frontier.requests[].cost_usd', 'float', 'USD', True, 'API ledger (null for Codex replay)', 'measured', 'B, C, D, E (API)'),
    ('frontier.requests[].status', 'str', 'ok|error category', False, 'record', 'measured', 'B, C, D, E'),
    ('frontier.requests[].request_sha256', 'str', 'sha256', True, 'artifact/packet hashes', 'identity', 'C, D, E'),
    ('frontier.requests[].response_sha256', 'str', 'sha256', True, 'guidance/diagnosis text hash', 'identity', 'C, D, E'),
    ('frontier.requests[].upfront', 'bool', '', False, 'generated before the run (C/D)', 'identity', 'C, D'),
    ('frontier.n_requests', 'int', 'requests', False, 'len(requests)', 'derived', 'all'),
    ('frontier.cost_usd', 'float', 'USD', True, 'sum of request costs; null if any request has no measured cost', 'measured', 'all'),
    ('frontier.wait_seconds_during_run', 'float', 's', False, 'E diagnosis wait + B coder latency', 'measured', 'B, E'),
    ('frontier.provider_failures', 'int', 'requests', False, 'requests with status != ok', 'measured', 'B, C, D, E'),
    ('condition.guidance', 'object', '', True, 'generated, delivered, sha256, generation cost/latency', 'measured', 'C, D'),
    ('condition.diagnosis', 'object', '', True, 'trigger, hashes, delivery, after-effects', 'measured', 'E'),
    ('time.wall_seconds', 'float', 's', False, 'run_attempt wall (setup included)', 'measured', 'all'),
    ('time.local_coding_seconds', 'float', 's', True, 'frozen run() duration', 'measured', 'all'),
    ('time.local_inference_seconds', 'float', 's', True, '= local_inference.total_inference_seconds', 'measured', 'A, C, D, E'),
    ('time.frontier_seconds', 'float', 's', False, 'frontier.wait_seconds_during_run (upfront guidance excluded)', 'measured', 'all'),
    ('time.public_test_seconds', 'float', 's', False, 'judge-public calls', 'measured', 'all'),
    ('time.sandbox_tool_seconds', 'float', 's', False, 'other sandbox commands', 'measured', 'all'),
    ('time.orchestration_seconds', 'float', 's', True, 'local_coding - inference - tools - tests - frontier - self-plan', 'derived', 'all'),
    ('time.equal_opportunity_seconds', 'float', 's', True, 'local_coding minus frontier wait and self-plan (the 600 s budget clock)', 'derived', 'all'),
    ('cost.api_cost_usd_run', 'float', 'USD', True, 'frontier requests made during the run', 'measured', 'B, E (API)'),
    ('cost.api_cost_usd_upfront', 'float', 'USD', True, 'guidance generation (one-off; amortize over attempts sharing the artifact)', 'measured', 'C, D (API)'),
    ('cost.gpu_memory_sample', 'object', '', True, 'nvidia-smi before/after (not GPU active time)', 'measured', 'A, C, D, E'),
    ('cost.modelled_local_energy_kwh', 'float', 'kWh', True, 'local_inference_seconds x assumed watts; only if assumptions given', 'modelled', 'A, C, D, E'),
    ('cost.modelled_local_cost_usd', 'float', 'USD', True, 'energy x assumed price; only if assumptions given', 'modelled', 'A, C, D, E'),
    ('cost.modelling_assumptions', 'object', '', True, 'watts and price supplied by the caller', 'configuration', 'A, C, D, E'),
]


def _iso(value):
    if not value:
        return None
    text = re.sub(r'(\.\d{6})\d+', r'\1', str(value)).replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError:
        return None


def _usage(usage):
    usage = usage or {}
    usage = usage.get('codex_reported', usage)   # Codex-authored artifacts nest Codex's own counts
    details = usage.get('completion_tokens_details') or {}
    prompt = usage.get('prompt_tokens_details') or {}
    return {'input_tokens': usage.get('prompt_tokens', usage.get('input_tokens')),
            'output_tokens': usage.get('completion_tokens', usage.get('output_tokens')),
            'reasoning_tokens': details.get('reasoning_tokens', usage.get('reasoning_output_tokens')),
            'cached_input_tokens': prompt.get('cached_tokens', usage.get('cached_input_tokens'))}


def _sum(values):
    values = [v for v in values if v is not None]
    return round(sum(values), 6) if values else None


def frontier_requests(record):
    requests = []
    provenance = record.get('guidance_provenance') or {}
    if provenance:
        artifact = {}
        try:
            artifact = read_json(provenance['artifact'])
        except Exception:
            pass
        requests.append({'type': 'guidance', 'prompt_id': provenance.get('prompt_id'), 'provider': provenance.get('provider'),
                         'utc': provenance.get('created_utc'), **_usage(artifact.get('usage')),
                         'latency_seconds': provenance.get('latency_seconds'), 'cost_usd': provenance.get('cost_usd'),
                         'status': 'ok', 'request_sha256': artifact.get('user_message_sha256'),
                         'response_sha256': sha256_text(artifact['text']) if artifact.get('text') else None, 'upfront': True})
    diagnosis = record.get('diagnosis') or {}
    if diagnosis.get('frontier_requested'):
        response = diagnosis.get('response') or {}
        packet = diagnosis.get('packet') or {}
        requests.append({'type': 'diagnosis', 'prompt_id': diagnosis.get('prompt_id'),
                         'provider': response.get('provider', diagnosis.get('provider')), 'utc': diagnosis.get('requested_utc'),
                         **_usage(response.get('usage')),
                         'latency_seconds': response.get('latency_seconds', diagnosis.get('frontier_wait_seconds')),
                         'cost_usd': response.get('cost_usd'), 'status': diagnosis.get('error_category') or 'ok',
                         'request_sha256': packet.get('user_message_sha256') or packet.get('candidate_sha256'),
                         'response_sha256': diagnosis.get('diagnosis_sha256'), 'upfront': False})
    coder = record.get('coder') or {}
    for call in (coder.get('calls') or []) if coder.get('provider') != 'scripted' else []:  # scripted = test device
        requests.append({'type': 'coder_turn', 'prompt_id': None, 'provider': coder.get('provider'), 'utc': call.get('utc'),
                         **_usage(call.get('usage')),
                         'latency_seconds': call.get('latency_seconds', call.get('harness_wall_seconds')),
                         'cost_usd': call.get('cost_usd'), 'status': 'ok', 'request_sha256': None, 'response_sha256': None,
                         'upfront': False})
    return requests


def build(run_dir, *, energy_watts=None, usd_per_kwh=None):
    run_dir = Path(run_dir)
    record = read_json(run_dir / 'result.json')
    agent_dir = run_dir / ('agent-' + record['run_id'])
    frozen = read_json(agent_dir / 'result.json') if (agent_dir / 'result.json').exists() else {}
    responses = read_json(agent_dir / 'ollama-responses.json') if (agent_dir / 'ollama-responses.json').exists() else []
    messages = read_json(agent_dir / 'trajectory.json')['messages'] if (agent_dir / 'trajectory.json').exists() else []
    hidden_path = run_dir.parent / 'eval' / f"{record['run_id']}.json"
    hidden = read_json(hidden_path) if hidden_path.exists() else {}
    events = [e for e in frozen.get('events') or [] if 'command' in e]
    tests = [e for e in events if e.get('recognized_public_test')]
    profile = frozen.get('profile_config') or record.get('profile_config') or {}
    spec = read_json(run_dir / 'spec.json') if (run_dir / 'spec.json').exists() else {}
    local = not record.get('coder')

    # agent behaviour from the sandbox events (snapshot hash after every action)
    failed, previous, writes, unchanged, rewrites_failed, hashes = set(), None, 0, 0, 0, set()
    for event in events:
        digest = event.get('source_sha256')
        if digest:
            hashes.add(digest)
        if event.get('recognized_public_test'):
            if event.get('public_status') != 'pass' and digest:
                failed.add(digest)
        elif isinstance(event.get('command'), str) and WRITE.search(event['command']):
            writes += 1
            unchanged += digest is not None and digest == previous
            rewrites_failed += digest in failed
        previous = digest if digest is not None else previous
    assistant = [m.get('content') for m in messages if m.get('role') == 'assistant']

    # timeline: model call k <-> response k; calls are assistant messages and FormatError messages, in order
    times = {}
    if local and responses:
        start = _iso(responses[0].get('created_at'))
        start = start - (responses[0].get('total_duration') or 0) / 1e9 if start else None
        call = -1
        for message in messages[2:]:
            kind = (message.get('extra') or {}).get('interrupt_type')
            if message.get('role') == 'assistant' or kind == 'FormatError':
                call += 1
            if message.get('role') == 'assistant' and call < len(responses) and start:
                at = _iso(responses[call].get('created_at'))
                actions = (message.get('extra') or {}).get('actions') or []
                if at and actions:
                    times.setdefault('first_action', at - start)
                    if TEST.fullmatch(actions[0].get('command') or ''):
                        times.setdefault('first_test', at - start)
        executable = next((e for e in tests if {'AC', 'WA'} & set(((e.get('judge') or {}).get('verdict_counts') or {}))), None)
        if executable is not None and 'first_test' in times:
            # the executable candidate's test is the n-th public test; its request time is the n-th test call
            n = tests.index(executable)
            test_calls = []
            call = -1
            for message in messages[2:]:
                kind = (message.get('extra') or {}).get('interrupt_type')
                if message.get('role') == 'assistant' or kind == 'FormatError':
                    call += 1
                actions = (message.get('extra') or {}).get('actions') or [] if message.get('role') == 'assistant' else []
                if actions and TEST.fullmatch(actions[0].get('command') or '') and call < len(responses):
                    test_calls.append(_iso(responses[call].get('created_at')))
            if n < len(test_calls) and test_calls[n] and start:
                times['first_executable'] = test_calls[n] - start

    requests = frontier_requests(record)
    run_costs = [r['cost_usd'] for r in requests if not r['upfront']]
    upfront_costs = [r['cost_usd'] for r in requests if r['upfront']]
    diagnosis = record.get('diagnosis') or {}
    frontier_wait = (record.get('frontier_wait_seconds') or 0.0) + sum(
        (r['latency_seconds'] or 0) for r in requests if r['type'] == 'coder_turn')
    self_plan = record.get('self_plan')
    inference_seconds = _sum((r.get('total_duration') or 0) / 1e9 for r in responses) if responses else None
    public_seconds = round(sum(e.get('elapsed_seconds') or 0 for e in tests), 3)
    tool_seconds = round(sum(e.get('elapsed_seconds') or 0 for e in events if not e.get('recognized_public_test')), 3)
    coding = record.get('local_coding_seconds')
    plan_seconds = (self_plan or {}).get('wall_seconds') or 0.0
    orchestration = None
    if coding is not None:
        orchestration = round(coding - (inference_seconds or 0) - tool_seconds - public_seconds - frontier_wait
                              - plan_seconds, 3)
    energy = cost_local = None
    if energy_watts is not None and inference_seconds is not None:
        energy = round(inference_seconds * energy_watts / 3.6e6, 8)
        cost_local = round(energy * usd_per_kwh, 8) if usd_per_kwh is not None else None
    guidance_state = record.get('guidance') or {}
    attempts = [json.loads(line) for line in (run_dir / 'attempts.jsonl').read_text(encoding='utf-8').splitlines()
                if line.strip()] if (run_dir / 'attempts.jsonl').exists() else []
    re_cases = sum(((a.get('result') or {}).get('verdict_counts') or {}).get('RE', 0) for a in attempts)
    final_public = (attempts[-1].get('result') or {}).get('status') if attempts else 'none'
    context_overflow = bool(local and responses and (record.get('frozen_error') or {}).get('error_type') == 'APIConnectionError'
                            and (responses[-1].get('prompt_eval_count') or 0) + (responses[-1].get('eval_count') or 0)
                            >= (profile.get('context') or 16384) - 1024)
    out = {
        'schema': SCHEMA, 'built_utc': utc_now(),
        'identity': {
            'run_id': record['run_id'], 'task_id': record['task_id'], 'condition': record['condition'],
            'seed': record.get('seed'), 'batch': record.get('batch'),
            'agent_config_id': (record.get('agent_config') or {}).get('id', 'frozen-v6'),
            'agent_config_sha256': (record.get('agent_config') or {}).get('definition_sha256'),
            'guidance_prompt_id': (record.get('guidance_provenance') or {}).get('prompt_id'),
            'injection': record.get('injection'),
            'diagnosis_prompt_id': diagnosis.get('prompt_id'), 'diagnosis_delivery': diagnosis.get('delivery_template'),
            'source_commit': (record.get('source') or {}).get('commit'), 'source_dirty': (record.get('source') or {}).get('dirty'),
            'coding_model': record.get('coding_model'), 'coding_model_digest': record.get('model_digest') if local else None,
            'profile': record.get('profile'), 'profile_config': profile or None,
            'frontier_provider': next((r['provider'] for r in requests), None),
            'frontier_requested_model': record.get('guidance_model') or (record.get('coder') or {}).get('model'),
            'frontier_observed_model': (record.get('guidance_provenance') or {}).get('observed_model')
            or (diagnosis.get('response') or {}).get('observed_model'),
            'dataset_revision': LCB_REVISION,
            'judge_version': (record.get('judge_public') or {}).get('judge_version'),
            'judge_public_tests_sha256': (record.get('judge_public') or {}).get('tests_sha256'),
            'guidance_artifact_sha256': (record.get('guidance_provenance') or {}).get('artifact_sha256'),
            'frozen_files_verified': (record.get('frozen_verification') or {}).get('frozen_files_verified'),
            'sampler_wire_verified': record.get('sampler_wire_verified') if local else None,
            'host': record.get('host_identity'), 'host_backend': record.get('host_backend'),
        },
        'correctness': {
            'candidate_produced': record.get('submission_sha256') is not None,
            'submitted': record.get('raw_exit_status') == 'Submitted', 'public_tests_invoked': len(attempts),
            'public_pass': any((a.get('result') or {}).get('status') == 'pass' for a in attempts),
            'final_public_status': final_public, 'public_runtime_error_cases': re_cases,
            'hidden_status': hidden.get('status'), 'hidden_passed': hidden.get('passed'), 'hidden_total': hidden.get('total'),
            'exit_status': record.get('exit_status'), 'raw_exit_status': record.get('raw_exit_status'),
            'infrastructure_failure': (record.get('exit_status') == 'infra_error' or bool(record.get('setup_error'))) and not context_overflow,
            'setup_error': record.get('setup_error'),
            'context_overflow': context_overflow,
        },
        'local_inference': {
            'calls': len(responses), 'prompt_tokens': _sum(r.get('prompt_eval_count') for r in responses) if responses else None,
            'completion_tokens': _sum(r.get('eval_count') for r in responses) if responses else None,
            'reasoning_tokens': None,
            'thinking_chars': sum(len((r.get('message') or {}).get('thinking') or '') for r in responses) if responses else None,
            'max_prompt_tokens': max((r.get('prompt_eval_count') or 0) for r in responses) if responses else None,
            'context_tokens_limit': profile.get('context') if local else None,
            'output_tokens_limit': profile.get('output_tokens') if local else None,
            'prompt_eval_seconds': _sum((r.get('prompt_eval_duration') or 0) / 1e9 for r in responses) if responses else None,
            'eval_seconds': _sum((r.get('eval_duration') or 0) / 1e9 for r in responses) if responses else None,
            'load_seconds': _sum((r.get('load_duration') or 0) / 1e9 for r in responses) if responses else None,
            'total_inference_seconds': inference_seconds,
            'truncated_responses': sum(r.get('done_reason') == 'length' for r in responses),
            'format_errors': record.get('format_errors') or 0,
            'self_plan': {k: self_plan.get(k) for k in ('delivered', 'truncated', 'prompt_tokens', 'completion_tokens',
                                                        'prompt_eval_seconds', 'eval_seconds', 'load_seconds',
                                                        'wall_seconds', 'text_sha256', 'error')} if self_plan else None,
        },
        'agent': {
            'actions': record.get('n_actions'), 'repairs': record.get('n_repairs'), 'model_calls': record.get('model_calls') or 0,
            'source_writes': writes, 'distinct_sources': len(hashes), 'unchanged_writes': unchanged,
            'rewrites_of_failed_candidate': rewrites_failed,
            'repeated_responses': sum(1 for a, b in zip(assistant, assistant[1:]) if a == b),
            'public_test_attempts': len(attempts),
            'seconds_to_first_valid_action': _round(times.get('first_action')),
            'seconds_to_first_executable_candidate': _round(times.get('first_executable')),
            'seconds_to_first_public_test': _round(times.get('first_test')),
        },
        'frontier': {
            'requests': requests, 'n_requests': len(requests),
            'cost_usd': round(sum(r['cost_usd'] for r in requests), 6) if requests and all(r['cost_usd'] is not None for r in requests) else (0.0 if not requests else None),
            'wait_seconds_during_run': round(frontier_wait, 3),
            'provider_failures': sum(r['status'] != 'ok' for r in requests),
        },
        'condition': {
            'guidance': {'generated': bool(record.get('guidance_provenance')), 'delivered': guidance_state.get('delivered'),
                         'contract_text_injected': guidance_state.get('contract_text_injected', guidance_state.get('delivered')),
                         'artifact_sha256': (record.get('guidance_provenance') or {}).get('artifact_sha256'),
                         'generation_cost_usd': (record.get('guidance_provenance') or {}).get('cost_usd'),
                         'generation_latency_seconds': (record.get('guidance_provenance') or {}).get('latency_seconds'),
                         'reused_across_seeds': None} if record.get('guidance_provenance') else None,
            'diagnosis': {k: diagnosis.get(k) for k in (
                'trigger_observed', 'trigger_reason', 'trigger_action', 'frontier_requested', 'frontier_returned', 'delivered',
                'error_category', 'frontier_wait_seconds', 'local_actions_after', 'public_tests_after',
                'candidate_changed_after', 'public_pass_after', 'later_public_failures', 'diagnosis_sha256',
                'diagnosis_words')} | {'failed_candidate_sha256': (diagnosis.get('packet') or {}).get('candidate_sha256'),
                                       'public_report_sha256': (diagnosis.get('packet') or {}).get('report_sha256')}
            if diagnosis else None,
        },
        'time': {
            'wall_seconds': record.get('wall_seconds'), 'local_coding_seconds': coding,
            'local_inference_seconds': inference_seconds, 'frontier_seconds': round(frontier_wait, 3),
            'public_test_seconds': public_seconds, 'sandbox_tool_seconds': tool_seconds,
            'orchestration_seconds': orchestration,
            'equal_opportunity_seconds': round(coding - (record.get('frontier_wait_seconds') or 0.0) - plan_seconds, 3)
            if coding is not None else None,
        },
        'cost': {
            'api_cost_usd_run': _sum(run_costs) if run_costs else 0.0,
            'api_cost_usd_upfront': _sum(upfront_costs) if upfront_costs else None,
            'gpu_memory_sample': record.get('gpu'),
            'modelled_local_energy_kwh': energy, 'modelled_local_cost_usd': cost_local,
            'modelling_assumptions': {'watts': energy_watts, 'usd_per_kwh': usd_per_kwh} if energy_watts is not None else None,
        },
    }
    if spec.get('agent') and out['identity']['agent_config_id'] != spec['agent']:
        out['identity']['agent_config_mismatch'] = spec['agent']
    return out


def _round(value):
    return round(value, 3) if value is not None else None


def write(run_dir, **kwargs):
    document = build(run_dir, **kwargs)
    write_json(Path(run_dir) / 'measurement.json', document)
    return document


def schema_markdown():
    lines = ['| Field | Type | Unit | Nullable | Source / computation | Kind | Applies to |', '| --- | --- | --- | --- | --- | --- | --- |']
    for path, kind_type, unit, nullable, source, kind, applies in FIELDS:
        lines.append(f'| `{path}` | {kind_type} | {unit} | {"yes" if nullable else "no"} | {source} | {kind} | {applies} |')
    return '\n'.join(lines)


def flatten(document, prefix=''):
    """Dotted keys -> values (lists and objects kept whole), for schema conformance checks."""
    out = {}
    for key, value in document.items():
        name = f'{prefix}{key}'
        if isinstance(value, dict) and name.count('.') < 1 and name not in ('identity.host',):
            out |= flatten(value, name + '.')
        else:
            out[name] = value
    return out


def conforms(document):
    """Problems if a built document lacks a documented field or carries an undocumented top-level field."""
    documented = {p for p, *_ in FIELDS if '[]' not in p}
    present = set(flatten(document))
    problems = [f'missing field {p}' for p in sorted(documented - present)]
    problems += [f'undocumented field {p}' for p in sorted(present - documented)
                 if p not in ('built_utc', 'identity.agent_config_mismatch')]
    for request in document.get('frontier', {}).get('requests', []):
        for p, *_ in FIELDS:
            if p.startswith('frontier.requests[].') and p.split('.')[-1] not in request:
                problems.append(f'request missing {p}')
    return problems
