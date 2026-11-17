"""One attempt or one independent judge. Candidate code runs only in existing Docker sandboxes."""
import argparse
import json
import time
import traceback
from pathlib import Path
from shared import baseline,ROOT,REPO,DATA,MODEL,MODEL_DIGEST,PROFILE,CONFIG,SEED,JUDGE,VENDOR,options,extract,ONE_SHOT_PROMPT,read,save,digest
import litellm
from judge_watch import score


def inference(args):
    out=args.output;budget=max(1,int(args.deadline-time.monotonic()-5))
    if args.condition=='A':
        # Observational exception logging only; same existing agent prompt, code,
        # sampler and actions. The legacy runner otherwise swallows typed causes.
        original=baseline.TextModel._query
        def observed(self,*a,**kw):
            try:return original(self,*a,**kw)
            except Exception as exc:
                chain=[];seen=set();current=exc
                while current and id(current) not in seen:
                    seen.add(id(current));chain.append(type(current).__module__+'.'+type(current).__name__)
                    current=current.__cause__ or current.__context__
                save(out/'model-exception.json',{'chain':chain,'traceback':traceback.format_exc()})
                raise
        baseline.TextModel._query=observed
        r=baseline.run(args.task,out,MODEL,PROFILE,seed=SEED,actions=10,repairs=3,seconds=budget)
        save(out/'pilot_budget.json',{'outer_wall_cap':120,'active_budget_after_startup_and_finalization_reserve':budget})
        return
    out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    task=read(args.task/'task.json');save(out/'task.json',task)
    messages=[{'role':'system','content':ONE_SHOT_PROMPT},{'role':'user','content':task['statement']}]
    save(out/'prompt.json',messages)
    capture=baseline.RawCapture(out/'ollama-responses.json');litellm.callbacks=[capture]
    record={'condition':'B','model':MODEL,'seed':SEED,'profile_config':CONFIG,'model_calls':0,'status':'InfrastructureError',
            'outer_wall_cap':120,'events':[],'public_tests':[],'format_errors':0}
    try:
        baseline.exclusive_gpu()
        assert next(x['digest'] for x in baseline.api(11435,'/api/tags')['models'] if x['name']==MODEL)==MODEL_DIGEST
        kwargs={'api_base':baseline.ENDPOINT,'num_ctx':16384,'num_predict':4096,'temperature':.2,'seed':SEED,
                'num_retries':0,'timeout':max(.1,args.deadline-time.monotonic()-5),'keep_alive':'10m','think':False,
                'extra_body':{'options':options()}}
        save(out/'configuration.json',{'model':'ollama_chat/'+MODEL,'model_kwargs':kwargs,'messages':messages})
        record['model_calls']=1
        result=litellm.completion(model='ollama_chat/'+MODEL,messages=messages,**kwargs)
        save(out/'completion.json',json.loads(result.model_dump_json()))
        text=result.choices[0].message.content or ''
        (out/'generated.txt').write_text(text,encoding='utf-8')
        source,format_status=extract(text);record['format_status']=format_status
        if source is not None:
            (out/'solution.py').write_text(source,encoding='utf-8');record['status']='Generated'
            record['submission_sha256']=digest(out/'solution.py')
        else:record.update(status='FormattingFailure',format_errors=1)
    except Exception as exc:
        record.update(error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc())
        chain=[];seen=set();current=exc
        while current and id(current) not in seen:
            seen.add(id(current));chain.append(type(current).__module__+'.'+type(current).__name__)
            current=current.__cause__ or current.__context__
        save(out/'model-exception.json',{'chain':chain,'traceback':traceback.format_exc()})
    finally:
        raw=capture.responses
        record.update(elapsed_seconds=time.monotonic()-started,token_telemetry_complete=len(raw)==record['model_calls'],
            sampler_wire_verified=bool(capture.requests) and all(x.get('options')==options() and x.get('think') is False
                and not x.get('tools') for x in capture.requests),
            inference={k:sum(x.get(k,0) for x in raw) for k in ('eval_count','prompt_eval_count','eval_duration','prompt_eval_duration','load_duration')})
        save(out/'result.json',record);litellm.callbacks=[]


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['infer','judge']);p.add_argument('--condition',choices=['A','B'])
    p.add_argument('--task',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--deadline',type=float)
    p.add_argument('--private',type=Path);args=p.parse_args()
    if args.mode=='judge':save(args.output/'evaluation.json',score(args.output,args.private,VENDOR,JUDGE))
    else:inference(args)
