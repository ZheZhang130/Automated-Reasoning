"""Run the frozen practical configuration against a trusted public task bundle."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from optlib import REPO, ROOT, digest, read


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seed',type=int,default=2108)
    parser.add_argument('--challenger',action='store_true',help='Use the explicitly evaluated alternative')
    args=parser.parse_args()
    selection_path=ROOT/'final_selection.json'
    selection=read(selection_path)
    recommendation=read(ROOT/'final_recommendation.json')
    if recommendation['selection_sha256']!=digest(selection_path):
        raise RuntimeError('Recommendation does not match the frozen selection')
    for name,expected in selection['runtime_sha256'].items():
        if digest(REPO/name)!=expected:raise RuntimeError('Frozen source changed: '+name)
    profile=selection['challenger'] if args.challenger else recommendation['recommended_profile']
    if read(ROOT/'profiles.json')[profile]!=selection['frozen_configurations'][profile]:
        raise RuntimeError('Frozen configuration changed')
    for image,expected in selection['images'].items():
        actual=json.loads(subprocess.check_output(['docker','image','inspect',image],text=True))[0]['Id']
        if actual!=expected['image_id']:raise RuntimeError('Frozen Docker image changed: '+image)
    script=REPO/'local_eval_v2/runtime.py' if profile=='heredoc-v6-16k-common' else ROOT/'runtime_opt.py'
    command=[sys.executable,str(script),'--task',str(args.task),'--output',str(args.output),
             '--model',selection['model'],'--profile',profile,'--seed',str(args.seed),
             '--seconds','600','--actions','20','--repairs','3']
    raise SystemExit(subprocess.call(command))


if __name__=='__main__':main()
