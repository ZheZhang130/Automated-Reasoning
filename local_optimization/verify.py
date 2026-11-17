"""Read-only integrity verification for archived sources, transports and controls."""
import argparse
import json
from pathlib import Path

from optlib import DATA, MODEL, ROOT, digest, read, save


def verify(batch):
    plan=read(batch/'plan.json')
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
        expected=profile['sampler']|{'num_ctx':profile['context'],'num_predict':profile['output_tokens'],'temperature':profile['temperature'],'seed':job['seed']}
        for wire in requests:
            if wire['model']!=MODEL or wire['options']!=expected or wire.get('think') is not profile['thinking']:
                raise ValueError('Wire configuration mismatch: '+job['key'])
        if len(requests)!=result['model_calls'] or (len(responses)!=result['model_calls'] and result['status']!='ModelTimeout'):
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
        if judge['status']!=read(slot/'complete.json')['evaluation']:
            raise ValueError('Judge outcome mismatch')
        complete+=1
    report={'batch':str(batch),'planned':len(plan['jobs']),'verified_complete':complete,'remaining':partial,
            'source_files_verified':len(plan['source_sha256'])}
    print(json.dumps(report),flush=True)
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
