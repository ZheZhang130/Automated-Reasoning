import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    A = list(map(int, input_data[1:]))

    # Precompute prefix distinct counts
    prefix_distinct = [0] * N
    seen = set()
    for i in range(N):
        seen.add(A[i])
        prefix_distinct[i] = len(seen)

    # Precompute suffix distinct counts
    suffix_distinct = [0] * N
    seen = set()
    for i in range(N - 1, -1, -1):
        seen.add(A[i])
        suffix_distinct[i] = len(seen)

    # Compute max sum
    max_sum = 0
    for i in range(N - 1):
        # Split after index i (0-based), so left is A[0..i], right is A[i+1..N-1]
        left_distinct = prefix_distinct[i]
        right_distinct = suffix_distinct[i + 1]
        total = left_distinct + right_distinct
        if total > max_sum:
            max_sum = total

    print(max_sum)

if __name__ == "__main__":
    solve()
