"""Create a paired, derived analysis view; no inference, judging or source copies."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from optlib import ROOT, digest, on_e, read, save


def combine(args):
    output=on_e(args.output)
    output.mkdir(parents=True,exist_ok=False)
    profiles={};tasks={};points={};sources=[];first=None
    for batch in args.batches:
        plan=read(batch/'plan.json')
        if first is None:first=plan
        for key in ('revision','source_sha256','evaluator_revision'):
            if plan['manifest'][key]!=first['manifest'][key]:raise ValueError('Incompatible dataset/evaluator provenance')
        sources.append({'path':str(batch/'plan.json'),'sha256':digest(batch/'plan.json')})
        if (batch/'judge-addendum.json').exists():
            sources.append({'path':str(batch/'judge-addendum.json'),'sha256':digest(batch/'judge-addendum.json'),'kind':'judge_observability_addendum'})
        for profile,config in plan['profiles'].items():
            if profile not in args.profiles:continue
            if profile in profiles and config!=profiles[profile]:raise ValueError('Profile changed between source cohorts')
            profiles[profile]=config
        for task in plan['manifest']['tasks']:
            if task['task_id'] in tasks and task!=tasks[task['task_id']]:raise ValueError('Task metadata/hash changed')
            tasks[task['task_id']]=task
        for job in plan['jobs']:
            if job['profile'] not in args.profiles:continue
            completion=batch/'runs'/job['key']/'complete.json'
            if not completion.exists():continue
            point=(job['task_id'],job['seed'],job['profile'])
            if point in points:raise ValueError('Duplicate task/seed/profile; choose one original experiment explicitly')
            points[point]=(job,read(completion),{'path':str(completion),'sha256':digest(completion)})
    if set(profiles)!=set(args.profiles):raise ValueError('Unknown requested profile')
    paired=set.intersection(*[{(t,s) for t,s,p in points if p==profile} for profile in args.profiles])
    if args.tasks:paired={k for k in paired if k[0] in args.tasks}
    if not paired:raise ValueError('No paired task/seed points')
    jobs=[];completions=[]
    for task,seed in sorted(paired):
        for profile in args.profiles:
            job,completion,origin=points[(task,seed,profile)]
            jobs.append(job)
            save(output/'runs'/job['key']/'complete.json',completion|{'derived_from':origin})
            completions.append(origin)
    manifest=first['manifest']|{'tasks':[tasks[t] for t in sorted({t for t,s in paired})]}
    save(output/'plan.json',{'kind':'derived_paired_analysis_only','manifest':manifest,'profiles':profiles,'jobs':jobs,
        'source_plans':sources,'source_completions':completions,'source_sha256':{},
        'note':'Read-only pointers to original measured attempts; no duplicated inference or benchmark outcomes.'})
    subprocess.run([sys.executable,str(ROOT/'analyze.py'),str(output)],check=True)
    print(json.dumps({'derived_comparison':str(output),'paired_task_seed_points':len(paired),'attempts':len(jobs)}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--batches',type=Path,nargs='+',required=True)
    p.add_argument('--profiles',nargs='+',required=True);p.add_argument('--tasks',nargs='+')
    p.add_argument('--output',type=Path,required=True);combine(p.parse_args())
