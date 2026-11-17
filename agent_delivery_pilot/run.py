"""One bounded three-way diagnostic, reusing the prior hard-deadline supervisor."""
import hashlib
import importlib.metadata
import shutil
import subprocess
import sys
import time
from pathlib import Path
from pilot_common import ROOT,REPO,DATA,MODEL,MODEL_DIGEST,VENDOR,JUDGE,GPU_LOCK,EVALUATOR,A2_PROMPT,baseline,previous,old_module,Lock,read,save,digest
from optlib import sources


def main():
    manifest=read(DATA/'manifest.json')
    assert digest(ROOT/'forensics.json')==manifest['forensics_sha256']
    if (DATA/'execution.json').exists():raise RuntimeError('Single execution only: no timer reset or extra trials')
    assert subprocess.check_output(['git','-C',str(VENDOR),'rev-parse','HEAD'],text=True).strip()==EVALUATOR
    assert not subprocess.check_output(['git','-C',str(VENDOR),'status','--porcelain'],text=True).strip()
    images={image:baseline.v3.isolation_preflight(image,Path('E:/DockerDesktop')) for image in (baseline.v3.IMAGE,JUDGE)}
    assert not baseline.api(11434,'/api/ps')['models']
    assert next(x['digest'] for x in baseline.api(11435,'/api/tags')['models'] if x['name']==MODEL)==MODEL_DIGEST
    hashes=sources()|{str(p.relative_to(REPO)):digest(p) for folder in (previous.ROOT,ROOT) for p in folder.glob('*.py')}
    for relative,checksum in hashes.items():
        target=DATA/'frozen-source'/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(REPO/relative,target);assert digest(target)==checksum
    worker=DATA/'frozen-source/agent_delivery_pilot/run_attempt.py'
    legacy=old_module('run');legacy.DATA=DATA
    with Lock(GPU_LOCK):
        started=time.monotonic();work_deadline=started+2075
        execution={'started_unix':time.time(),'started_monotonic':started,'hard_deadline_monotonic':started+2100,
            'source_sha256':hashes,'images':images,'packages':{p:importlib.metadata.version(p) for p in ('mini-swe-agent','litellm','pydantic')},
            'ollama':baseline.api(11435,'/api/version'),'manifest_sha256':digest(DATA/'manifest.json'),
            'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
            'ordering':'CPU sandbox/parser controls; two A2 synthetic fixtures; frozen E/M/M/M tasks, rotate A/A2/B order by task index',
            'single_intervention':'A2 system prompt only','sanity_included_in_ceiling':True}
        save(DATA/'execution.json',execution);status='complete';error=None
        try:
            control=legacy.supervised([sys.executable,str(DATA/'frozen-source/agent_delivery_pilot/synthetic_controls.py')],
                DATA/'control-process',40,DATA/'sanity-controls')
            if control['returncode'] or not (DATA/'sanity-controls/checks.json').exists():raise RuntimeError('Synthetic backend/parser controls failed')
            for name in ('dev-negative-squares','dev-functional-distinct'):
                task=DATA.parent/'eval-v2/development-v5/public'/name;private=DATA.parent/'eval-v2/development-v5/private'/(name+'.json')
                key='sanity-'+name+'-A2'
                assert legacy.attempt(worker,task,private,key,'A2',work_deadline)=='pass'
                r=read(DATA/'runs'/key/'result.json')
                if not any(t['returncode']==0 for t in r['public_tests']):raise RuntimeError('A2 fixture did not expose real recognized public feedback')
            for index,task in enumerate(manifest['tasks']):
                order=['A','A2','B'];offset=index%3;order=order[offset:]+order[:offset]
                for condition in order:
                    public=DATA/'dataset/public'/task['task_id'];private=DATA/'dataset/evaluator_private'/(task['task_id']+'.json')
                    assert {p.name:digest(p) for p in public.iterdir()}==task['public_sha256'] and digest(private)==task['private_row_sha256']
                    assert next(x['digest'] for x in baseline.api(11435,'/api/tags')['models'] if x['name']==MODEL)==MODEL_DIGEST
                    key='osa-'+task['task_id']+'-'+condition
                    legacy.attempt(worker,public,private,key,condition,work_deadline)
                    wire=read(DATA/'runs'/key/'ollama-requests.json')
                    expected=A2_PROMPT if condition=='A2' else previous.ONE_SHOT_PROMPT if condition=='B' else baseline.PROMPT
                    assert wire[0]['messages'][0]['content'].strip()==expected.strip()
        except TimeoutError as exc:status='budget_stop';error=str(exc)
        except Exception as exc:status='infrastructure_stop';error=str(exc)
        finally:
            try:baseline.api(11435,'/api/generate',{'model':MODEL,'keep_alive':0},timeout=3)
            except Exception:pass
            elapsed=time.monotonic()-started
            save(DATA/'status.json',{'status':status,'error':error,'experimental_wall_seconds':elapsed,'ceiling_seconds':2100,
                                   'within_hard_ceiling':elapsed<2100,'finished_unix':time.time()})
            print(read(DATA/'status.json'),flush=True)
    assert all(digest(REPO/p)==h for p,h in manifest['protected_repository_sha256'].items())
    assert all(digest(p)==h for p,h in read(ROOT/'forensics.json')['original_artifact_sha256'].items())
    if status=='infrastructure_stop':raise RuntimeError(error)


if __name__=='__main__':main()
