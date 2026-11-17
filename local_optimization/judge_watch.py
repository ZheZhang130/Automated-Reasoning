"""Same official judge/limits, with owned-container resource-failure evidence."""
import json
import subprocess
import time
import uuid
from pathlib import Path

from optlib import BASELINE, digest, read, save
import runner as sandbox


def oom_events(name, since):
    result=sandbox.docker('events','--since',str(int(since)-1),'--until',str(time.time()+.1),
        '--filter','event=oom','--format','{{json .}}',timeout=10)
    events=[json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    return [e for e in events if e.get('Actor',{}).get('Attributes',{}).get('name')==name]


def score(run,row_path,vendor,image,*,judge_script=None):
    source=run/'solution.py'
    if not source.is_file():
        return {'status':'missing_submission'}
    judge_script=judge_script or BASELINE/'judge_lcb.py'
    name='csc2108-lcb-'+uuid.uuid4().hex[:12]
    payload={'source':source.read_text(encoding='utf-8'),'row':read(row_path)}
    started=time.time();exit_code=None
    arguments=['run','--name',name,'--rm','--pull','never','-i','--network','none',
        '--read-only','--memory','1g','--memory-swap','1g','--cpus','1','--pids-limit','64',
        '--user','65534:65534','--cap-drop','ALL','--security-opt','no-new-privileges',
        '--tmpfs','/tmp:rw,nosuid,size=128m,mode=1777',
        '--mount',f'type=bind,src={vendor},dst=/opt/lcb,readonly',
        '--mount',f'type=bind,src={judge_script},dst=/judge.py,readonly',image,'python','-I','/judge.py']
    save(run/'judge-launch.json',{'name':name,'arguments':arguments,'started_unix':started,
        'source_sha256':digest(source),'private_row_sha256':digest(row_path),'judge_script_sha256':digest(judge_script),
        'wrapper_sha256':digest(__file__),'host_timeout_seconds':180})
    stdout=stderr=''
    try:
        result=sandbox.docker(*arguments,input=json.dumps(payload),timeout=180)
        stdout,stderr=result.stdout,result.stderr;exit_code=result.returncode
        markers=[line for line in stdout.splitlines() if line.startswith('CSC2108_EVALUATION=')]
        raw=json.loads(markers[-1].split('=',1)[1])
    except Exception as exc:
        stdout=getattr(exc,'stdout','') or '';stderr=getattr(exc,'stderr','') or ''
        exit_code=getattr(exc,'returncode',None)
        raw={'status':'infrastructure_error','error_type':type(exc).__name__,'error':str(exc)}
    finally:
        subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=15)
    if isinstance(stdout,bytes):stdout=stdout.decode('utf-8',errors='replace')
    if isinstance(stderr,bytes):stderr=stderr.decode('utf-8',errors='replace')
    (run/'judge.stdout.txt').write_text(stdout,encoding='utf-8')
    (run/'judge.stderr.txt').write_text(stderr,encoding='utf-8')
    save(run/'official-evaluator.json',raw)
    try:
        events=oom_events(name,started)
        resource={'name':name,'oom_events':events,'exit_code':exit_code,'wall_seconds':time.time()-started}
    except Exception as exc:
        events=[]
        resource={'name':name,'telemetry_error':str(exc),'exit_code':exit_code,'wall_seconds':time.time()-started}
    save(run/'resource-events.json',resource)
    if raw['status']=='infrastructure_error' and (events or exit_code==124):
        return {'status':'candidate_resource_failure','resource':'memory_1g' if events else 'judge_wall_175s',
                'official_evaluator_status':raw['status'],'official_evaluator':raw,
                'evidence':'resource-events.json','exit_code':exit_code}
    return raw
