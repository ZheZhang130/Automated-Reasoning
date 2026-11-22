# Special judge for abc396_e (any minimum-sum good sequence accepted). Runs in an isolated container; prints counts.
import pathlib, subprocess
ok = bad = 0
for case in sorted(pathlib.Path('/h').glob('*.in')):
    data = case.read_text().split(); n, m = int(data[0]), int(data[1])
    edges = [tuple(map(int, data[2 + 3 * i: 5 + 3 * i])) for i in range(m)]
    want = case.with_suffix('.out').read_text().split()
    try:
        got = subprocess.run(['python3', '-I', '/c/submission.py'], stdin=case.open(), capture_output=True, text=True, timeout=10).stdout.split()
        if want == ['-1']:
            good = got == ['-1']
        else:
            a = [0] + list(map(int, got))
            good = (len(got) == n and all(v >= 0 for v in a) and all(a[x] ^ a[y] == z for x, y, z in edges)
                    and sum(a) == sum(map(int, want)))
    except Exception:
        good = False
    ok += good; bad += not good
print(f'special_judge: {ok} pass, {bad} fail')
