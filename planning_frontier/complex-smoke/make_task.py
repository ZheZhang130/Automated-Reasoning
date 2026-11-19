import json
from pathlib import Path
root = Path('/tmp/csc2108-dynamic-connectivity')
root.mkdir(exist_ok=True)
statement = """Maintain an initially empty undirected multigraph on vertices 1..N.
Input: N Q, then Q operations. '+ u v' inserts one copy of edge {u,v}.
'- u v' removes one copy; that copy is guaranteed to exist. '? u v' asks
whether u and v are connected. Print YES or NO for each query, in order.
Parallel edges and self-loops are allowed. Removing one parallel copy must
preserve connectivity if another remains. Edges are undirected even if the
endpoint order is reversed. A vertex is connected to itself.
1 <= N <= 200000, 1 <= Q <= 200000. Aim for near-linear or polylogarithmic
amortized processing; recomputing the graph for every query is too slow.
Read stdin and write stdout as a standalone Python program saved at
/workspace/solution.py. Run python -I /public/check.py to test.
"""
(root/'task.json').write_text(json.dumps(dict(task_id="synthetic-dynamic-connectivity",version="1",statement=statement,submission_path="solution.py")))
cases = [
("3 5\n+ 1 2\n? 1 3\n+ 2 3\n? 1 3\n? 3 3\n", "NO\nYES\nYES"),
("2 7\n+ 1 2\n+ 2 1\n- 1 2\n? 1 2\n- 2 1\n? 1 2\n? 1 1\n", "YES\nNO\nYES"),
("4 9\n+ 1 2\n+ 2 3\n+ 1 3\n- 1 2\n? 1 2\n- 1 3\n? 1 2\n+ 2 4\n? 3 4\n", "YES\nNO\nYES"),
("2 4\n+ 1 1\n? 1 2\n- 1 1\n? 1 1\n","NO\nYES"),
("2 1\n? 1 2\n","NO"),
("2 6\n+ 1 2\n- 1 2\n+ 2 1\n? 1 2\n- 1 2\n? 2 1\n","YES\nNO"),
]
(root/'public_tests.json').write_text(json.dumps(cases))
(root/'check.py').write_text("""import json, subprocess
from pathlib import Path
cases=json.loads(Path('/public/public_tests.json').read_text())
for index,(inputs, expected) in enumerate(cases,1):
    r=subprocess.run(['python','-I','/workspace/solution.py'], input=inputs, text=True, capture_output=True, timeout=4)
    assert r.returncode==0 and r.stdout.split()==expected.split(), (index,inputs,expected,r.stdout,r.stderr[-1000:])
print('PUBLIC TESTS: %s/%s passed' % (len(cases),len(cases)))
""")
print(root)
