# Runs inside an isolated container: candidate at /c/submission.py, hidden cases at /h. Prints counts only.
import pathlib, subprocess, sys
ok = bad = 0
for case in sorted(pathlib.Path('/h').glob('*.in')):
    want = case.with_suffix('.out').read_text().split()
    try:
        got = subprocess.run(['python3', '-I', '/c/submission.py'], stdin=case.open(), capture_output=True, text=True, timeout=10).stdout.split()
        good = len(got) == len(want) and all(abs(float(a) - float(b)) <= 1e-8 * max(1.0, abs(float(b))) for a, b in zip(got, want))
    except Exception:
        good = False
    ok += good; bad += not good
print(f'tolerance_1e-8: {ok} pass, {bad} fail')
