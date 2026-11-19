"""Independent synthetic verification. Candidates execute only in Docker."""
import collections
import json
import random
import subprocess
import sys
import time
from pathlib import Path

cases=[]
for seed in range(30):
    rng=random.Random(seed)
    n=12
    edges=collections.Counter()
    operations=[]
    answers=[]
    for _ in range(150):
        roll=rng.random()
        if roll<.35:
            u,v=rng.randrange(n),rng.randrange(n)
            edges[tuple(sorted((u,v)))]+=1
            operations.append(f'+ {u+1} {v+1}')
        elif roll<.55 and edges:
            edge=rng.choice(list(edges))
            edges[edge]-=1
            if not edges[edge]:del edges[edge]
            operations.append(f'- {edge[1]+1} {edge[0]+1}')
        else:
            u,v=rng.randrange(n),rng.randrange(n)
            adj=[[] for _ in range(n)]
            for a,b in edges:
                adj[a].append(b);adj[b].append(a)
            seen={u};stack=[u]
            while stack:
                for w in adj[stack.pop()]:
                    if w not in seen:
                        seen.add(w);stack.append(w)
            answers.append('YES' if v in seen else 'NO')
            operations.append(f'? {u+1} {v+1}')
    cases.append((f'{n} {len(operations)}\n'+'\n'.join(operations)+'\n',answers))
n=25000
operations=[f'+ {i} {i+1}' for i in range(1,n)]
answers=[]
for _ in range(20000):
    operations.extend([f'? 1 {n}', '- 1 2', f'? 1 {n}', '+ 1 2'])
    answers.extend(['YES','NO'])
cases.append((f'{n} {len(operations)}\n'+'\n'.join(operations)+'\n',answers))

for path in sys.argv[1:]:
    path=Path(path).resolve()
    report={"candidate":str(path),"passed":0,"total":len(cases),"failures":[]}
    if not path.exists():
        report["error"]="missing candidate"
    else:
        for index,(inputs,expected) in enumerate(cases):
            start=time.monotonic()
            try:
                r=subprocess.run(['docker','run','--rm','-i','--network','none','--read-only',
                    '--memory','512m','--cpus','1','--pids-limit','32','--user','65534:65534',
                    '--cap-drop','ALL','--security-opt','no-new-privileges',
                    '--mount',f'type=bind,src={path},dst=/solution.py,readonly',
                    'python:3.11-slim-bookworm','python','-I','/solution.py'],
                    input=inputs,text=True,capture_output=True,timeout=12)
                passed=r.returncode==0 and r.stdout.split()==expected
                if passed:report["passed"]+=1
                else:report["failures"].append({"case":index,"returncode":r.returncode,"stderr":r.stderr[-500:]})
            except subprocess.TimeoutExpired:
                report["failures"].append({"case":index,"error":"timeout"})
            if index==30:report["stress_seconds"]=time.monotonic()-start
    destination=path.parent/'independent-check.json'
    destination.write_text(json.dumps(report,indent=2))
    print(json.dumps(report),flush=True)
