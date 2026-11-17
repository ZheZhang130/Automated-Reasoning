"""Read-only integrity verification for archived sources, transports and controls."""
import argparse
import json
from pathlib import Path

from optlib import DATA, MODEL, ROOT, digest, read, save


def verify(batch):
    plan=read(batch/'plan.json')
    if plan.get('kind')=='derived_paired_analysis_only':
        for source in plan['source_plans']+plan['source_completions']:
            if digest(source['path'])!=source['sha256']:raise ValueError('Derived comparison source changed')
    if (batch/'judge-addendum.json').exists():
        addition=read(batch/'judge-addendum.json')
        if digest(addition['path'])!=addition['sha256']:
            raise ValueError('Judge observability addendum changed')
    for relative, expected in plan['source_sha256'].items():
        if digest(batch/'frozen-source'/relative)!=expected:
            raise ValueError('Archived source changed: '+relative)
    complete=0
    partial=[]
    for job in plan['jobs']:
        slot=batch/'runs'/job['key']
        if not (slot/'complete.json').exists():
            partial.append(job['key']);continue
        attempt=Path(read(slot/'complete.json')['attempt'])
        result=read(attempt/'result.json')
        requests=read(attempt/'ollama-requests.json')
        responses=read(attempt/'ollama-responses.json')
        profile=plan['profiles'][job['profile']]
        assessment=read(attempt/'timeout-assessment.json') if (attempt/'timeout-assessment.json').exists() else {}
        if assessment and (digest(attempt/'result.json')!=assessment['result_sha256'] or digest(attempt/'trajectory.json')!=assessment['trajectory_sha256']):
            raise ValueError('Timeout assessment evidence changed')
        expected=profile['sampler']|{'num_ctx':profile['context'],'num_predict':profile['output_tokens'],'temperature':profile['temperature'],'seed':job['seed']}
        for wire in requests:
            if wire['model']!=MODEL or wire['options']!=expected or wire.get('think') is not profile['thinking']:
                raise ValueError('Wire configuration mismatch: '+job['key'])
        if len(requests)!=result['model_calls'] or (len(responses)!=result['model_calls'] and assessment.get('effective_status',result['status'])!='ModelTimeout'):
            raise ValueError('Unexplained missing transport evidence')
        if profile.get('native_history')=='fixed':
            for request in requests:
                calls=[c for m in request['messages'] for c in m.get('tool_calls',[])]
                observations=[m for m in request['messages'] if m['role']=='tool']
                if len(calls)!=len(observations) or any(m.get('tool_name')!='bash' for m in observations):
                    raise ValueError('Native history mismatch')
        if (attempt/'solution.py').exists() and digest(attempt/'solution.py')!=result['submission_sha256']:
            raise ValueError('Extracted source changed')
        judge=read(attempt/'private_evaluation.json')
        if judge['status']=='candidate_resource_failure':
            judged=[p for p in sorted(attempt.glob('judge-attempt-*')) if (p/'resource-events.json').exists()]
            if not judged:raise ValueError('Resource failure has no owned-container evidence')
            resource=read(judged[-1]/'resource-events.json');launch=read(judged[-1]/'judge-launch.json')
            if resource['name']!=launch['name']:raise ValueError('Judge container ownership mismatch')
            if judge['resource']=='memory_1g' and not any(e.get('Actor',{}).get('Attributes',{}).get('name')==launch['name'] for e in resource['oom_events']):
                raise ValueError('Missing matching OOM event')
            if judge['resource']=='judge_wall_175s' and resource['exit_code']!=124:
                raise ValueError('Missing container timeout exit code')
        if judge['status']!=read(slot/'complete.json')['evaluation']:
            raise ValueError('Judge outcome mismatch')
        complete+=1
    report={'batch':str(batch),'planned':len(plan['jobs']),'verified_complete':complete,'remaining':partial,
            'source_files_verified':len(plan['source_sha256'])}
    print(json.dumps({k:v for k,v in report.items() if k!='remaining'} | {'remaining_count':len(partial)}),flush=True)
    return report


def baseline():
    hashes=read(DATA/'baseline-evidence-sha256.json')
    for path,expected in hashes.items():
        if digest(path)!=expected:
            raise ValueError('Original baseline evidence changed: '+path)
    print(json.dumps({'original_baseline_files_verified':len(hashes)}))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('batch',type=Path,nargs='?')
    p.add_argument('--baseline',action='store_true')
    args=p.parse_args()
    if args.batch: verify(args.batch)
    if args.baseline: baseline()
