"""Annotate the known frozen wrapper-classification defect without altering raw evidence."""
import argparse
import json
import shutil
import time
from pathlib import Path

from optlib import JUDGE, VENDOR, digest, on_e, read, save
from pilot import score


def assess(slot):
    slot=on_e(slot)
    attempt=slot/'attempt-01'
    if (slot/'complete.json').exists() or (attempt/'timeout-assessment.json').exists():
        raise ValueError('Never replace an existing assessment/completion')
    result=read(attempt/'result.json')
    trajectory=read(attempt/'trajectory.json')
    trace=trajectory['messages'][-1].get('extra',{}).get('traceback','')
    if not (result['status']=='InfrastructureError' and result.get('error_type')=='APIConnectionError'
            and 'litellm.Timeout: Connection timed out' in result.get('error','') and 'httpx.ReadTimeout' in trace
            and result['elapsed_seconds']>=.99*result['time_limit_seconds'] and result['sampler_wire_verified']
            and result.get('unobserved_model_calls')==1):
        raise ValueError('Not the established expired-wall-time wrapper defect')
    assessment={'effective_status':'ModelTimeout','classification':'declared_resource_budget_expired',
        'raw_status_retained':result['status'],'reason':'Pinned LiteLLM wraps httpx.ReadTimeout as APIConnectionError; actual traceback, timeout message and elapsed task wall independently establish the expiration. No inference is retried.',
        'result_sha256':digest(attempt/'result.json'),'trajectory_sha256':digest(attempt/'trajectory.json'),
        'unobserved_model_calls':1,'unobserved_output_token_upper_bound':result['profile_config']['output_tokens'],
        'assessed_unix':time.time()}
    judge=attempt/'judge-timeout-assessment'
    judge.mkdir()
    if (attempt/'solution.py').exists():shutil.copyfile(attempt/'solution.py',judge/'solution.py')
    evaluation=score(judge,Path(read(slot.parent.parent/'plan.json')['tasks'][result['task_id']]['private']),VENDOR,JUDGE)
    if evaluation['status']=='infrastructure_error':raise RuntimeError('Judge did not complete')
    save(judge/'evaluation.json',evaluation)
    save(attempt/'private_evaluation.json',evaluation)
    save(attempt/'timeout-assessment.json',assessment)
    save(slot/'complete.json',{'attempt':str(attempt),'evaluation':evaluation['status'],'finished':time.time(),'assessment':'timeout-assessment.json'})
    print(json.dumps({'status':assessment['effective_status'],'official':evaluation['status'],'raw_result_changed':False}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('slot',type=Path);assess(p.parse_args().slot)
