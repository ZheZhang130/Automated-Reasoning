"""Select six fresh tasks using metadata and visible-interface eligibility only."""
import collections
import hashlib
import json
import shutil
import subprocess
from shared import ROOT,REPO,DATA,CACHE,REVISION,EVALUATOR,MODEL,MODEL_DIGEST,PROFILE,CONFIG,SEED,read,save,digest


def prepare():
    if DATA.exists():raise RuntimeError('Refusing to replace an existing pilot directory')
    excluded=set(read(REPO/'local_optimization/results/scored_task_ids.json')['exclude_from_future_fresh_validation'])
    assert len(excluded)==65
    old_contests=set()
    for p in [REPO/'local_eval_v2/evaluation_manifest.json',*(REPO/'local_optimization').glob('*_manifest.json')]:
        old_contests.update((t['platform'],str(t['contest_id'])) for t in read(p)['tasks'])
    expected=read(REPO/'local_optimization/heldout_manifest.json')['source_sha256']
    assert digest(CACHE)==expected
    pool=[]
    for number,line in enumerate(CACHE.open(encoding='utf-8')):
        row=json.loads(line);key=row['platform']+'-'+row['question_id']
        contest=(row['platform'],str(row['contest_id']))
        if key in excluded:old_contests.add(contest);continue
        public=json.loads(row['public_test_cases']);fn=json.loads(row['metadata']).get('func_name')
        supported=(public and all(t['testtype']=='stdin' for t in public) and not fn) or (
            isinstance(fn,str) and fn.isidentifier() and 'class Solution' in row['starter_code']
            and not any(x in row['starter_code'] for x in ('TreeNode','ListNode','Node[')))
        if not supported or not public or '<img' in row['question_content'] or '![' in row['question_content']:continue
        pool.append({k:row[k] for k in ('platform','difficulty','contest_id','contest_date')}|
                    {'task_id':key,'line_number':number,'function_name':fn})
    chosen=[];used=set()
    for difficulty,count in [('easy',2),('medium',3),('hard',1)]:
        platforms=collections.Counter()
        for _ in range(count):
            eligible=[x for x in pool if x['difficulty']==difficulty and (x['platform'],str(x['contest_id'])) not in used]
            fresh=[x for x in eligible if (x['platform'],str(x['contest_id'])) not in old_contests]
            if fresh:eligible=fresh
            if not eligible:raise RuntimeError('Insufficient eligible tasks')
            pick=min(eligible,key=lambda x:(platforms[x['platform']],x['platform'],hashlib.sha256(
                ('CSC2108-one-shot-pilot-v1:'+x['task_id']).encode()).hexdigest()))
            chosen.append(pick);pool.remove(pick);platforms[pick['platform']]+=1
            used.add((pick['platform'],str(pick['contest_id'])))
            pick['previous_contest_fallback']=(pick['platform'],str(pick['contest_id'])) in old_contests
    assert len(chosen)==6 and not excluded&{x['task_id'] for x in chosen}
    DATA.mkdir(parents=True)
    wanted={x['line_number']:x for x in chosen}
    for number,line in enumerate(CACHE.open(encoding='utf-8')):
        if number not in wanted:continue
        info=wanted[number];row=json.loads(line);public=DATA/'dataset/public'/info['task_id'];public.mkdir(parents=True)
        fn=info['function_name'];starter=row.get('starter_code','')
        interface=('Implement the provided Solution class method '+fn if fn else 'Write a standalone Python stdin/stdout program')
        statement=row['question_content']+'\n\nRequired interface: '+interface+'. Save the source as solution.py.'
        statement+='\n\nProvided starter code:\n```python\n'+starter+'\n```'
        save(public/'task.json',{'task_id':info['task_id'],'version':REVISION,'statement':statement,'submission_path':'solution.py'})
        tests=json.loads(row['public_test_cases'])
        save(public/'public_tests.json',[t|{'fn_name':fn} for t in tests] if fn else tests)
        shutil.copyfile(REPO/'local_eval_v2/public_check.py',public/'check.py')
        if starter.strip():(public/'solution.py').write_text(starter,encoding='utf-8')
        private=DATA/'dataset/evaluator_private'/(info['task_id']+'.json');save(private,row)
        info.update(public_sha256={p.name:digest(p) for p in public.iterdir()},private_row_sha256=digest(private),
                    shared_statement_sha256=hashlib.sha256(statement.encode()).hexdigest())
    tracked=subprocess.check_output(['git','ls-files','local_baseline','local_eval_v2','local_optimization'],cwd=REPO,text=True).splitlines()
    manifest={'dataset_revision':REVISION,'dataset_sha256':expected,'evaluator_revision':EVALUATOR,
        'model':MODEL,'model_digest':MODEL_DIGEST,'profile':PROFILE,'configuration':CONFIG,'seed':SEED,
        'selection_rule':'2easy/3medium/1hard; exclude65; prefer unevaluated contests; one task per contest; platform round robin within difficulty then salted SHA256 order. Eligibility identical to prior study. No private tests decoded.',
        'excluded':sorted(excluded),'previous_contests':sorted(old_contests),'tasks':chosen,
        'protected_repository_sha256':{p:digest(REPO/p) for p in tracked},
        'agent_budget':'shortened baseline:120s total outer wall,10actions,3repair groups; reserve5s within wall for finalization',
        'one_shot_budget':'one call,4096tokens,120s total outer wall; reserve5s within wall for finalization',
        'global_ceiling_seconds':2100,'shutdown_reserve_seconds':25,'sanity_included_in_global_ceiling':True}
    save(DATA/'manifest.json',manifest);save(ROOT/'manifest.json',manifest)
    print(json.dumps({'selected':[(t['task_id'],t['difficulty'],t['previous_contest_fallback']) for t in chosen]}))


if __name__=='__main__':prepare()
