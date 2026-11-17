"""A2 replaces one prompt in memory; A and B use the prior worker verbatim."""
import argparse
import hashlib
from pathlib import Path
from types import SimpleNamespace
from pilot_common import baseline,previous,PROFILE,A2_PROFILE,A2_PROMPT,JUDGE,VENDOR,old_module,save


def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['infer','judge']);p.add_argument('--condition',choices=['A','A2','B'])
    p.add_argument('--task',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--deadline',type=float);p.add_argument('--private',type=Path)
    args=p.parse_args();worker=old_module('worker')
    if args.mode=='judge':save(args.output/'evaluation.json',worker.score(args.output,args.private,VENDOR,JUDGE));return
    if args.condition=='A2':baseline.PROMPT=A2_PROMPT
    forwarded=SimpleNamespace(**vars(args));forwarded.condition='B' if args.condition=='B' else 'A'
    worker.inference(forwarded)
    prompt=previous.ONE_SHOT_PROMPT if args.condition=='B' else baseline.PROMPT
    save(args.output/'protocol.json',{'condition':args.condition,'profile':A2_PROFILE if args.condition=='A2' else PROFILE,
        'base_generation_profile':PROFILE,'system_prompt':prompt,'system_prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest()})


if __name__=='__main__':main()
