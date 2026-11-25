s = input().strip()
expected = 'i'
insertions = 0

for ch in s:
    if ch != expected:
        insertions += 1
    expected = 'o' if ch == 'i' else 'i'

if expected == 'o':
    insertions += 1

print(insertions)
