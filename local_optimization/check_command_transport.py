"""Isolated transport fixture, not a benchmark solution; no model inference."""
import hashlib
import json
import time
from pathlib import Path

from optlib import DATA, save
from runtime_opt import Environment
import runner as sandbox
from minisweagent.exceptions import InterruptAgentFlow


def main():
    root=DATA/'diagnostics/long-command-transport'
    root.mkdir(exist_ok=False)
    public=DATA.parent/'eval-v2/development-v5/public/dev-negative-squares'
    sandbox.isolation_preflight(sandbox.IMAGE,Path('E:/DockerDesktop'))
    source=("# transport padding: 'quotes', \"double\", $literal, `literal`, Ω\n"*3500)+"print('STREAM_OK')\n"
    command="cat > /workspace/solution.py <<'PY'\n"+source+"PY\n"
    records=[]
    for streaming in (False,True):
        events=[]
        env=Environment(budget=sandbox.Budget(10,3),deadline=time.monotonic()+60,evidence=events,
            image=sandbox.IMAGE,cwd='/workspace',run_args=sandbox.container_args(public),container_timeout='90s',
            env={'PYTHONDONTWRITEBYTECODE':'1','HOME':'/tmp'})
        env.stream_large_commands=streaming
        try:
            try:
                result=env.execute({'command':command})
                status='executed'
            except InterruptAgentFlow as exc:
                status=exc.messages[-1].get('extra',{}).get('exit_status')
                result=events[-1] if events else {}
            record={'streaming':streaming,'status':status,'command_bytes':len(command.encode('utf-8')),
                    'returncode':result.get('returncode'),'exception_info':result.get('exception_info')}
            if streaming:
                candidate=env.snapshot()
                record['source_sha256']=hashlib.sha256(candidate).hexdigest()
                record['expected_sha256']=hashlib.sha256(source.encode('utf-8')).hexdigest()
                record['source_byte_exact']=candidate==source.encode('utf-8')
                output=env.execute({'command':'python -I /workspace/solution.py'})
                record['program_marker']=output['output'].strip()
                eof=env.execute({'command':('# padding\n'*2000)+"python -I -c \"import sys; print('EOF:' + repr(sys.stdin.read()))\""})
                record['stdin_is_eof']=eof['output'].strip()=="EOF:''"
                if not (record['source_byte_exact'] and record['stdin_is_eof'] and record['program_marker']=='STREAM_OK'):
                    raise RuntimeError('Streaming did not preserve command/source/stdin semantics')
            records.append(record)
            save(root/'results.json',records)
        finally:env.cleanup()
    if records[0]['status']=='executed':raise RuntimeError('Expected legacy Windows argv limitation did not reproduce')
    print(json.dumps(records),flush=True)


if __name__=='__main__':main()
