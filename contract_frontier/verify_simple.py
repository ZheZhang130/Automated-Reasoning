"""Independent synthetic signed-sum checks, executed inside Docker."""
import json
import subprocess
import sys
from pathlib import Path

candidate = Path(sys.argv[1]).resolve(strict=True)
script = """import json,subprocess
cases=[(0,0),(1,-1),(-9,-11),(10**50,-1),(-10**50,10**50),(123456789,987654321)]
passed=0
for a,b in cases:
    r=subprocess.run(['python','-I','/solution.py'],input=f'{a} {b}\\n',text=True,capture_output=True,timeout=3)
    if r.returncode==0 and r.stdout.split()==[str(a+b)]:passed+=1
print(json.dumps({'passed':passed,'total':len(cases)}))
"""
result = subprocess.run([
    "docker","run","--rm","--network","none","--read-only","--memory","256m",
    "--cpus","1","--pids-limit","32","--user","65534:65534","--cap-drop","ALL",
    "--security-opt","no-new-privileges","--mount",f"type=bind,src={candidate},dst=/solution.py,readonly",
    "python:3.11-slim-bookworm","python","-I","-c",script,
],capture_output=True,text=True,timeout=30,check=True)
record=json.loads(result.stdout)
(candidate.parent/"independent-check.json").write_text(json.dumps(record,indent=2))
print(json.dumps(record))
