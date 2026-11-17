"""Single-use pilot supervisor: includes sanity, inference and judging in one 35-minute ceiling."""
import importlib.metadata
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from shared import ROOT,REPO,DATA,MODEL,MODEL_DIGEST,JUDGE,VENDOR,GPU_LOCK,EVALUATOR,baseline,options,read,save,digest,Lock
from optlib import sources


def cleanup_owned(out):
    record=out/'container.json'
    if record.exists():
        owner=read(record);cid=owner['container_id']
        inspection=subprocess.run(['docker','inspect',cid],capture_output=True,text=True,timeout=3)
        if inspection.returncode==0:
            item=json.loads(inspection.stdout)[0]
            if item['Config'].get('Labels',{}).get('csc2108.eval-v2.run')!=owner['run_id']:
                raise RuntimeError('Refusing cleanup: container ownership mismatch')
            if not (out/'solution.py').exists():
                try:
                    candidate=baseline.v3.TaskEnvironment.snapshot(SimpleNamespace(container_id=cid))
                    if candidate is not None:
                        (out/'solution.py').write_bytes(candidate)
                        save(out/'supervisor-extraction.json',{'sha256':digest(out/'solution.py'),'reason':'Preserve unchanged sandbox source after supervised stop'})
                except Exception:pass
            subprocess.run(['docker','rm','-f',cid],capture_output=True,timeout=5)
    launch=out/'judge-launch.json'
    if launch.exists():
        name=read(launch)['name']
        if not name.startswith('csc2108-lcb-'):raise RuntimeError('Unexpected owned judge name')
        subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=5)


def supervised(command,out,seconds,ownership):
    out.parent.mkdir(parents=True,exist_ok=True)
    started=time.monotonic();timed_out=False
    with out.with_suffix('.stdout.txt').open('w',encoding='utf-8') as stdout,out.with_suffix('.stderr.txt').open('w',encoding='utf-8') as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        save(out.with_suffix('.process.json'),{'pid':child.pid,'command':command,'started_monotonic':started})
        try:child.wait(timeout=max(.1,seconds))
        except subprocess.TimeoutExpired:
            timed_out=True
            if child.poll() is None:
                subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True,timeout=3)
            try:child.wait(timeout=2)
            except subprocess.TimeoutExpired:pass
    if timed_out:cleanup_owned(ownership)
    result={'returncode':child.returncode,'supervisor_timeout':timed_out,'wall_seconds':time.monotonic()-started}
    save(out.with_suffix('.timing.json'),result)
    return result


def attempt(worker,task,private,key,condition,work_deadline):
    out=DATA/'runs'/key
    limit=min(120,work_deadline-time.monotonic())
    if limit<120:raise TimeoutError('Global budget: do not start a shortened attempt')
    info=supervised([sys.executable,str(worker),'infer','--condition',condition,'--task',str(task),
        '--output',str(out),'--deadline',str(time.monotonic()+120)],out,120,out)
    if not (out/'result.json').exists():
        save(out/'supervisor-result.json',{'status':'AttemptWallLimit' if info['supervisor_timeout'] else 'WorkerFailure'})
    else:
        r=read(out/'result.json')
        wire=read(out/'ollama-requests.json') if (out/'ollama-requests.json').exists() else []
        if not wire or not all(x.get('options')==options() and x.get('think') is False and x['model']==MODEL and not x.get('tools') for x in wire):
            raise RuntimeError('Actual model/sampler wire invariant failed')
        if wire[0]['messages'][1]['content']!=read(task/'task.json')['statement']:
            raise RuntimeError('Shared initial task text changed in transport')
        if r['status']=='InfrastructureError':
            exception=read(out/'model-exception.json') if (out/'model-exception.json').exists() else {}
            if not any(x.endswith(('ReadTimeout','TimeoutError')) for x in exception.get('chain',[])):
                raise RuntimeError('Genuine inference infrastructure failure; no retry')
            save(out/'timeout-assessment.json',{'effective_status':'ModelTimeout','original_result_sha256':digest(out/'result.json'),
                                               'typed_chain':exception['chain'],'raw_result_unchanged':True})
    if work_deadline-time.monotonic()<15:raise TimeoutError('Global budget before grading')
    judge=out/'judge';judge.mkdir()
    if (out/'solution.py').exists():shutil.copyfile(out/'solution.py',judge/'solution.py')
    timing=supervised([sys.executable,str(worker),'judge','--output',str(judge),'--private',str(private)],
        out/'grading',min(190,work_deadline-time.monotonic()),judge)
    if not (judge/'evaluation.json').exists():raise TimeoutError('Judge unfinished at supervisor deadline')
    evaluation=read(judge/'evaluation.json')
    if evaluation['status']=='infrastructure_error':raise RuntimeError('Judge infrastructure error; evidence retained')
    completed={'condition':condition,'task_id':read(task/'task.json')['task_id'],'evaluation':evaluation['status'],
               'inference_wall_seconds':info['wall_seconds'],'judge_wall_seconds':timing['wall_seconds']}
    save(out/'complete.json',completed)
    print(json.dumps(completed),flush=True)
    return evaluation['status']


def main():
    manifest=read(DATA/'manifest.json')
    if (DATA/'execution.json').exists():raise RuntimeError('Single pilot only: refusing another execution or timer reset')
    assert subprocess.check_output(['git','-C',str(VENDOR),'rev-parse','HEAD'],text=True).strip()==EVALUATOR
    assert not subprocess.check_output(['git','-C',str(VENDOR),'status','--porcelain'],text=True).strip()
    images={image:baseline.v3.isolation_preflight(image,Path('E:/DockerDesktop')) for image in (baseline.v3.IMAGE,JUDGE)}
    assert baseline.api(11434,'/api/ps')['models']==[]
    assert next(x['digest'] for x in baseline.api(11435,'/api/tags')['models'] if x['name']==MODEL)==MODEL_DIGEST
    hashes=sources()|{str(p.relative_to(REPO)):digest(p) for p in ROOT.glob('*.py')}
    for relative,checksum in hashes.items():
        target=DATA/'frozen-source'/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(REPO/relative,target);assert digest(target)==checksum
    worker=DATA/'frozen-source/one_shot_ablation/worker.py'
    synthetic=DATA/'sanity/public'
    shutil.copytree(DATA.parent/'eval-v2/development-v5/public/dev-negative-squares',synthetic)
    with Lock(GPU_LOCK):
        started=time.monotonic();work_deadline=started+2075
        execution={'started_unix':time.time(),'started_monotonic':started,'hard_deadline_monotonic':started+2100,
            'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
            'work_deadline_monotonic':work_deadline,'source_sha256':hashes,'images':images,
            'packages':{p:importlib.metadata.version(p) for p in ('mini-swe-agent','litellm','pydantic')},
            'ollama':baseline.api(11435,'/api/version'),'manifest_sha256':digest(DATA/'manifest.json'),
            'ordering':'sanity A/B; six selected tasks interleaved E/M/H/E/M/M, alternating A/B order by task index',
            'agent_prompt_sha256':__import__('hashlib').sha256(baseline.PROMPT.encode()).hexdigest()}
        save(DATA/'execution.json',execution)
        status='complete';error=None
        try:
            for condition in ('A','B'):
                outcome=attempt(worker,synthetic,DATA.parent/'eval-v2/development-v5/private/dev-negative-squares.json',
                                'sanity-'+condition,condition,work_deadline)
                if outcome!='pass':raise RuntimeError('Synthetic sanity failed; no benchmark runs authorized by harness')
            tasks=manifest['tasks']
            easy=[x for x in tasks if x['difficulty']=='easy'];medium=[x for x in tasks if x['difficulty']=='medium'];hard=[x for x in tasks if x['difficulty']=='hard']
            ordered=[easy[0],medium[0],hard[0],easy[1],medium[1],medium[2]]
            for index,task in enumerate(ordered):
                for condition in (('A','B') if index%2==0 else ('B','A')):
                    public=DATA/'dataset/public'/task['task_id'];private=DATA/'dataset/evaluator_private'/(task['task_id']+'.json')
                    assert {p.name:digest(p) for p in public.iterdir()}==task['public_sha256'] and digest(private)==task['private_row_sha256']
                    assert next(x['digest'] for x in baseline.api(11435,'/api/tags')['models'] if x['name']==MODEL)==MODEL_DIGEST
                    attempt(worker,public,private,'osa-'+task['task_id']+'-'+condition,condition,work_deadline)
        except TimeoutError as exc:status='budget_stop';error=str(exc)
        except Exception as exc:status='infrastructure_stop';error=str(exc)
        finally:
            try:baseline.api(11435,'/api/generate',{'model':MODEL,'keep_alive':0},timeout=3)
            except Exception:pass
            elapsed=time.monotonic()-started
            save(DATA/'status.json',{'status':status,'error':error,'experimental_wall_seconds':elapsed,'ceiling_seconds':2100,
                'within_hard_ceiling':elapsed<2100,'finished_unix':time.time()})
            print(json.dumps(read(DATA/'status.json')),flush=True)
    assert all(digest(REPO/p)==checksum for p,checksum in manifest['protected_repository_sha256'].items())
    if status=='infrastructure_stop':raise RuntimeError(error)


if __name__=='__main__':main()
