import sys
from sys import stdin

def solve():
    input_data = stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    N = int(next(iterator))
    A = [int(next(iterator)) for _ in range(N)]

    # Frequency array for values (values are 1..N)
    freq = [0] * (N + 1)
    for x in A:
        freq[x] += 1

    right_distinct = sum(1 for f in freq if f > 0)
    left_distinct = 0
    left_seen = [False] * (N + 1)

    max_sum = 0

    # Iterate split point i from 1 to N-1 (left subarray is A[0:i])
    for i in range(N - 1):
        x = A[i]
        if not left_seen[x]:
            left_distinct += 1
            left_seen[x] = True
        freq[x] -= 1
        if freq[x] == 0:
            right_distinct -= 1
        max_sum = max(max_sum, left_distinct + right_distinct)

    print(max_sum)

if __name__ == "__main__":
    solve()
