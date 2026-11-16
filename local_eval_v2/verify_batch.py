"""Read-only post-run verification of the frozen experimental contract."""
import argparse
from pathlib import Path

from batch import source_hashes
from common import ENDPOINT, digest, read, save
from runtime import PROMPT, NATIVE_PROMPT


def verify(batch):
    plan = read(batch / 'plan.json')
    assert source_hashes() == plan['source_sha256'], 'Frozen implementation changed'
    assert len(plan['jobs']) == len({j['key'] for j in plan['jobs']})
    complete = telemetry = 0
    exceptions = []
    for job in plan['jobs']:
        done_path = batch / 'runs' / job['key'] / 'complete.json'
        if not done_path.exists():
            continue
        done = read(done_path)
        assert done['job'] == job
        attempt = Path(done['attempt'])
        result = read(attempt / 'result.json')
        for key in ('model', 'profile', 'task_id', 'seed'):
            assert result[key] == job[key], (job['key'], key)
        assert result['actions'] <= plan['actions']
        assert result['repairs'] <= plan['repairs']
        assert result['public_sha256'] == plan['tasks'][job['task_id']]['public_sha256']
        assert read(attempt / 'private_evaluation.json')['status'] == done['official_status']
        if result['status'] == 'InfrastructureError' and not (attempt / 'configuration.json').exists():
            exceptions.append(job['key'])
            complete += 1
            continue
        config = read(attempt / 'configuration.json')['info']['config']
        assert result['isolation']['image_id'] == plan['images'][config['environment']['image']]['image_id']
        tag = next(t for t in result['tags']['models'] if t['name'] == job['model'])
        assert tag['digest'] == plan['model_digests'][job['model']]
        kwargs = config['model']['model_kwargs']
        prompt = PROMPT if plan['profile_config']['protocol'] == 'text' else NATIVE_PROMPT
        assert config['agent']['system_template'] == prompt
        assert config['model']['model_name'] == 'ollama_chat/' + job['model']
        assert kwargs['api_base'] == ENDPOINT
        assert kwargs['temperature'] == plan['profile_config'].get('temperature', 0)
        assert kwargs['num_ctx'] == plan['profile_config']['context']
        assert kwargs['num_predict'] == plan['profile_config']['output_tokens']
        assert kwargs['seed'] == job['seed']
        if job['model'].startswith('qwen3.5'):
            assert kwargs['think'] is plan['profile_config']['thinking']
        run_args = config['environment']['run_args']
        assert run_args[run_args.index('--network') + 1] == 'none'
        assert '--read-only' in run_args and '--cap-drop' in run_args
        mounts = [run_args[i + 1] for i, arg in enumerate(run_args) if arg == '--mount']
        assert len(mounts) == 1
        assert mounts[0] == 'type=bind,src=' + plan['tasks'][job['task_id']]['public'] + ',dst=/public,readonly'
        trajectory = read(attempt / 'trajectory.json')
        # Jinja's default rendering removes a final template newline.
        assert trajectory['messages'][0]['content'] == prompt.rstrip('\n')
        assert trajectory['messages'][1]['content'] == read(Path(plan['tasks'][job['task_id']]['public']) / 'task.json')['statement']
        raw = read(attempt / 'ollama-responses.json') if (attempt / 'ollama-responses.json').exists() else []
        assert len(raw) == result['inference']['calls_captured']
        if job['model'].startswith('qwen3.5') and not plan['profile_config']['thinking']:
            assert not any(r.get('message', {}).get('thinking') for r in raw)
        if plan['profile_config'].get('sampler'):
            requests = read(attempt / 'ollama-requests.json')
            expected = plan['profile_config']['sampler'] | {'num_ctx': plan['profile_config']['context'],
                'num_predict': plan['profile_config']['output_tokens'], 'temperature': plan['profile_config']['temperature'], 'seed': job['seed']}
            assert len(requests) == result['model_calls']
            assert all(r['options'] == expected for r in requests)
            assert result['sampler_wire_verified'] is True
        telemetry += bool(result.get('token_telemetry_complete'))
        if (attempt / 'solution.py').exists():
            assert digest(attempt / 'solution.py') == result['submission_sha256']
        complete += 1
    report = {'status': 'pass', 'completed_checked': complete, 'planned': len(plan['jobs']),
              'complete_raw_telemetry_runs': telemetry, 'pre_agent_infrastructure_exceptions': exceptions,
              'frozen_sources_unchanged': True}
    save(batch / 'verification.json', report)
    print(report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch', type=Path)
    verify(parser.parse_args().batch)
