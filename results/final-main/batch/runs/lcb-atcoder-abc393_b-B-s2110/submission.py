s = input().strip()
answer = 0
for j, ch in enumerate(s):
    if ch == 'B':
        for d in range(1, min(j, len(s) - 1 - j) + 1):
            if s[j - d] == 'A' and s[j + d] == 'C':
                answer += 1
print(answer)
