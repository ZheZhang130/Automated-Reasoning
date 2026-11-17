"""Resume only the bookkeeping gate, under the ORIGINAL deadline and unchanged frozen worker/prompt."""
import json
import re
import subprocess
import sys
import time
from pilot_common import ROOT,DATA,previous,A2_PROMPT,GPU_LOCK,MODEL,MODEL_DIGEST,baseline,old_module,Lock,read,save,digest


def genuine_fixture_feedback(result):
    for event in result.get('events',[]):
        if not re.search(r'^[ \t]*python -I /public/check\.py[ \t]*$',event.get('command',''),re.M):continue
        for line in event.get('output','').splitlines():
            if line.startswith('CSC2108_PUBLIC_RESULT=') and json.loads(line.split('=',1)[1]).get('status')=='pass':return True
    return False


def main():
    original=read(DATA/'execution.json');prior=read(DATA/'status.json');manifest=read(DATA/'manifest.json')
    if prior['status']!='infrastructure_stop' or list((DATA/'runs').glob('osa-*')):
        raise RuntimeError('Only a pre-benchmark sanity gate can continue; no benchmark retries')
    for completed in (DATA/'runs').glob('sanity-*/complete.json'):
        assert read(completed)['evaluation']=='pass' and genuine_fixture_feedback(read(completed.parent/'result.json'))
    assert (DATA/'sanity-controls/checks.json').exists()
    assert all(digest(DATA/'frozen-source'/p)==h for p,h in original['source_sha256'].items())
    stamp=str(time.time_ns())
    save(DATA/('status-at-sanity-gate-'+stamp+'.json'),prior)
    controller=DATA/'controller-continuations'/stamp
    controller.mkdir(parents=True)
    (controller/'source.py').write_bytes(__import__('pathlib').Path(__file__).read_bytes())
    save(controller/'continuation.json',{'source_sha256':digest(__file__),'started_unix':time.time(),
        'original_started_monotonic':original['started_monotonic'],'original_hard_deadline_monotonic':original['hard_deadline_monotonic'],
        'reason':'Sanity passed real compound public feedback and independent judging, but old gate demanded recognition by the narrow unchanged budget matcher.',
        'prompt_worker_sampler_unchanged':True,'completed_attempts_will_not_repeat':True})
    worker=DATA/'frozen-source/agent_delivery_pilot/run_attempt.py';legacy=old_module('run');legacy.DATA=DATA
    work_deadline=original['hard_deadline_monotonic']-25
    with Lock(GPU_LOCK):
        status='complete';error=None
        try:
            if work_deadline-time.monotonic()<120:raise TimeoutError('Original global deadline: no further work')
            for name in ('dev-negative-squares','dev-functional-distinct'):
                key='sanity-'+name+'-A2';out=DATA/'runs'/key
                if not (out/'complete.json').exists():
                    assert legacy.attempt(worker,DATA.parent/'eval-v2/development-v5/public'/name,
                        DATA.parent/'eval-v2/development-v5/private'/(name+'.json'),key,'A2',work_deadline)=='pass'
                assert read(out/'complete.json')['evaluation']=='pass' and genuine_fixture_feedback(read(out/'result.json'))
            for index,task in enumerate(manifest['tasks']):
                order=['A','A2','B'];offset=index%3;order=order[offset:]+order[:offset]
                for condition in order:
                    key='osa-'+task['task_id']+'-'+condition;out=DATA/'runs'/key
                    if (out/'complete.json').exists():continue
                    public=DATA/'dataset/public'/task['task_id'];private=DATA/'dataset/evaluator_private'/(task['task_id']+'.json')
                    assert {p.name:digest(p) for p in public.iterdir()}==task['public_sha256'] and digest(private)==task['private_row_sha256']
                    assert next(x['digest'] for x in baseline.api(11435,'/api/tags')['models'] if x['name']==MODEL)==MODEL_DIGEST
                    legacy.attempt(worker,public,private,key,condition,work_deadline)
                    wire=read(out/'ollama-requests.json')
                    expected=A2_PROMPT if condition=='A2' else previous.ONE_SHOT_PROMPT if condition=='B' else baseline.PROMPT
                    assert wire[0]['messages'][0]['content'].strip()==expected.strip()
        except TimeoutError as exc:status='budget_stop';error=str(exc)
        except Exception as exc:status='infrastructure_stop';error=str(exc)
        finally:
            try:baseline.api(11435,'/api/generate',{'model':MODEL,'keep_alive':0},timeout=3)
            except Exception:pass
            elapsed=time.monotonic()-original['started_monotonic']
            save(DATA/'status.json',{'status':status,'error':error,'experimental_wall_seconds':elapsed,'ceiling_seconds':2100,
                'within_hard_ceiling':elapsed<2100,'finished_unix':time.time(),'resumed_same_original_clock':True})
            print(read(DATA/'status.json'),flush=True)
    if status=='infrastructure_stop':raise RuntimeError(error)


if __name__=='__main__':main()
