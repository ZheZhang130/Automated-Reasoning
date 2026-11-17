"""No-inference controls: genuine sandbox writes/tests/repair and malformed-action rejection."""
import json
import time
from types import SimpleNamespace
import litellm
from minisweagent.exceptions import InterruptAgentFlow
from pilot_common import DATA,REPO,baseline,read,save


def main():
    out=DATA/'sanity-controls';out.mkdir(exist_ok=False)
    public=DATA.parent/'eval-v2/development-v5/public/dev-negative-squares'
    events=[];budget=baseline.v3.Budget(10,3)
    env=baseline.Environment(budget=budget,deadline=time.monotonic()+30,evidence=events,image=baseline.v3.IMAGE,cwd='/workspace',
        run_args=baseline.v3.container_args(public)+['--label','csc2108.eval-v2.run=delivery-synthetic-controls'],
        container_timeout='60s',env={'HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'})
    save(out/'container.json',{'container_id':env.container_id,'run_id':'delivery-synthetic-controls'})
    try:
        inspection=json.loads(baseline.v3.docker('inspect',env.container_id,timeout=5).stdout)[0]
        h=inspection['HostConfig'];assert h['NetworkMode']=='none' and h['ReadonlyRootfs'] and h['Memory']==512*1024**2
        assert h['PidsLimit']==64 and not h['Privileged'] and inspection['Config']['User']=='65534:65534'
        assert 'ALL' in h['CapDrop'] and any('no-new-privileges' in x for x in h['SecurityOpt'])
        binds=[x for x in inspection['Mounts'] if x['Type']=='bind'];assert len(binds)==1 and binds[0]['Destination']=='/public' and not binds[0]['RW']
        model=baseline.TextModel(model_name='ollama_chat/qwen3.5:9b',cost_tracking='ignore_errors',
            action_regex=r'```(?:mswea_bash_command|bash)\s*\n(.*?)\n```',format_error_template=baseline.FORMAT_ERROR)
        rejected=False
        try:model._parse_actions(litellm.ModelResponse(choices=[{'message':{'role':'assistant','content':'```mswea_bash_command\ntouch /workspace/SHOULD_NOT_EXIST'},'finish_reason':'length'}]))
        except InterruptAgentFlow as exc:
            rejected=exc.messages[0].get('extra',{}).get('interrupt_type')=='FormatError'
        assert rejected
        env.execute({'command':"cat > /workspace/solution.py <<'PY'\nprint(0)\nPY"})
        failed=env.execute({'command':'python -I /public/check.py'});assert failed['returncode']!=0 and events[-1]['recognized_public_test']
        correct=(DATA.parent/'optimization/diagnostics/dev-negative-squares--native-fixed-16k-4k/solution.py').read_text(encoding='utf-8')
        env.execute({'command':"cat > /workspace/solution.py <<'PY'\n"+correct+"\nPY"})
        passed=env.execute({'command':'python -I /public/check.py'});assert passed['returncode']==0 and budget.repairs==1
        result=env.execute({'command':"test ! -e /workspace/SHOULD_NOT_EXIST && printf REAL_SHELL_OK"});assert result['output'].strip()=='REAL_SHELL_OK'
        submitted=False
        try:env.execute({'command':'echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT'})
        except InterruptAgentFlow:submitted=True
        assert submitted
        save(out/'checks.json',{'isolation_verified':True,'malformed_action_rejected_without_execution':True,'complete_source_writes':True,
            'persistent_workspace':True,'real_shell_execution':True,'public_failure_then_changed_repair_and_pass':True,'repairs':budget.repairs,'submission_signal':True})
        save(out/'events.json',events)
    finally:env.cleanup()
    print('Sandbox/parser/real feedback/changed repair/submission controls passed; no model inference.')


if __name__=='__main__':main()
