"""Freeze one easy and three medium fresh tasks, excluding all 71 prior IDs."""
import collections
import hashlib
import json
import shutil
import subprocess
from pilot_common import ROOT,REPO,DATA,previous,CACHE,REVISION,EVALUATOR,CONFIG,SEED,MODEL,MODEL_DIGEST,A2_PROFILE,A2_PROMPT,baseline,read,save,digest


def main():
    if (DATA/'manifest.json').exists() or (DATA/'dataset').exists():raise RuntimeError('Never replace a frozen pilot dataset')
    excluded=set(read(REPO/'local_optimization/results/scored_task_ids.json')['exclude_from_future_fresh_validation'])
    old=read(REPO/'one_shot_ablation/manifest.json');excluded.update(t['task_id'] for t in old['tasks'])
    assert len(excluded)==71
    old_contests={tuple(x) for x in old['previous_contests']}
    old_contests.update((t['platform'],str(t['contest_id'])) for t in old['tasks'])
    assert digest(CACHE)==old['dataset_sha256']
    pool=[]
    for number,line in enumerate(CACHE.open(encoding='utf-8')):
        row=json.loads(line);key=row['platform']+'-'+row['question_id'];contest=(row['platform'],str(row['contest_id']))
        if key in excluded:old_contests.add(contest);continue
        public=json.loads(row['public_test_cases']);fn=json.loads(row['metadata']).get('func_name')
        supported=(public and all(t['testtype']=='stdin' for t in public) and not fn) or (
            isinstance(fn,str) and fn.isidentifier() and 'class Solution' in row['starter_code']
            and not any(x in row['starter_code'] for x in ('TreeNode','ListNode','Node[')))
        if supported and public and '<img' not in row['question_content'] and '![' not in row['question_content']:
            pool.append({k:row[k] for k in ('platform','difficulty','contest_id','contest_date')}|
                        {'task_id':key,'line_number':number,'function_name':fn})
    chosen=[];used=collections.Counter()
    for difficulty,count in [('easy',1),('medium',3)]:
        platforms=collections.Counter()
        for _ in range(count):
            eligible=[x for x in pool if x['difficulty']==difficulty]
            pick=min(eligible,key=lambda x:((x['platform'],str(x['contest_id'])) in old_contests,
                used[(x['platform'],str(x['contest_id']))],platforms[x['platform']],x['platform'],
                hashlib.sha256(('CSC2108-delivery-pilot-v1:'+x['task_id']).encode()).hexdigest()))
            chosen.append(pick);pool.remove(pick);platforms[pick['platform']]+=1;used[(pick['platform'],str(pick['contest_id']))]+=1
            pick['previous_contest_fallback']=(pick['platform'],str(pick['contest_id'])) in old_contests
    for number,line in enumerate(CACHE.open(encoding='utf-8')):
        info=next((x for x in chosen if x['line_number']==number),None)
        if info is None:continue
        row=json.loads(line);fn=info['function_name'];starter=row.get('starter_code','');public=DATA/'dataset/public'/info['task_id'];public.mkdir(parents=True)
        interface='Implement the provided Solution class method '+fn if fn else 'Write a standalone Python stdin/stdout program'
        statement=row['question_content']+'\n\nRequired interface: '+interface+'. Save the source as solution.py.'
        statement+='\n\nProvided starter code:\n```python\n'+starter+'\n```'
        save(public/'task.json',{'task_id':info['task_id'],'version':REVISION,'statement':statement,'submission_path':'solution.py'})
        tests=json.loads(row['public_test_cases']);save(public/'public_tests.json',[t|{'fn_name':fn} for t in tests] if fn else tests)
        shutil.copyfile(REPO/'local_eval_v2/public_check.py',public/'check.py')
        if starter.strip():(public/'solution.py').write_text(starter,encoding='utf-8')
        private=DATA/'dataset/evaluator_private'/(info['task_id']+'.json');save(private,row)
        info.update(public_sha256={p.name:digest(p) for p in public.iterdir()},private_row_sha256=digest(private),
                    shared_statement_sha256=hashlib.sha256(statement.encode()).hexdigest())
    protected=subprocess.check_output(['git','ls-files','local_baseline','local_eval_v2','local_optimization','one_shot_ablation'],cwd=REPO,text=True).splitlines()
    manifest={'dataset_revision':REVISION,'dataset_sha256':old['dataset_sha256'],'evaluator_revision':EVALUATOR,'model':MODEL,'model_digest':MODEL_DIGEST,
        'configuration':CONFIG,'seed':SEED,'tasks':chosen,'excluded':sorted(excluded),'previous_contests':sorted(old_contests),
        'selection_rule':'1easy/3medium; exclude71; rank by previously evaluated contest (false first), new contest reuse count, platform count within difficulty, platform name, salted SHA256; salt CSC2108-delivery-pilot-v1:',
        'intervention':'Only agent system prompt replacement, treated as one factor; no other inference/runtime/parser changes',
        'A2_profile':A2_PROFILE,'A2_prompt':A2_PROMPT,'A_prompt_sha256':hashlib.sha256(baseline.PROMPT.encode()).hexdigest(),
        'A2_prompt_sha256':hashlib.sha256(A2_PROMPT.encode()).hexdigest(),'one_shot_prompt_sha256':hashlib.sha256(previous.ONE_SHOT_PROMPT.encode()).hexdigest(),
        'outer_attempt_cap_seconds':120,'actions':10,'repairs':3,'shared_finalization_reserve_seconds':5,'global_ceiling_seconds':2100,
        'protected_repository_sha256':{p:digest(REPO/p) for p in protected},'forensics_sha256':digest(ROOT/'forensics.json')}
    save(ROOT/'manifest.json',manifest);save(DATA/'manifest.json',manifest)
    save(ROOT/'future_exclusions.json',{'previously_scored':sorted(excluded),'newly_selected':[t['task_id'] for t in chosen],
        'exclude_from_future_fresh_validation':sorted(excluded|{t['task_id'] for t in chosen})})
    print([(t['task_id'],t['difficulty'],t['previous_contest_fallback']) for t in chosen])


if __name__=='__main__':main()
