import subprocess
for inputs, expected in [('2 3\n','5'),('-4 1\n','-3'),('0 -8\n','-8')]:
    result = subprocess.run(['python','-I','/workspace/solution.py'], input=inputs, text=True, capture_output=True, timeout=3)
    assert result.returncode == 0 and result.stdout.strip() == expected, (inputs, expected, result.stdout, result.stderr)
print('PUBLIC TESTS: 3/3 passed')
