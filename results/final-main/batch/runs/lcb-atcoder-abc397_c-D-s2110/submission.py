import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    A = [int(x) for x in input_data[1:]]
    
    # Precompute distinct counts for all prefixes
    # distinct_prefix[i] = number of distinct elements in A[0:i+1]
    distinct_prefix = [0] * N
    seen = set()
    for i in range(N):
        seen.add(A[i])
        distinct_prefix[i] = len(seen)
    
    # Precompute distinct counts for all suffixes
    # distinct_suffix[i] = number of distinct elements in A[i:N]
    distinct_suffix = [0] * N
    seen = set()
    for i in range(N-1, -1, -1):
        seen.add(A[i])
        distinct_suffix[i] = len(seen)
    
    # Find max sum
    max_sum = 0
    for i in range(N-1):
        # Split after index i (0-based), so left is A[0:i+1], right is A[i+1:N]
        left_distinct = distinct_prefix[i]
        right_distinct = distinct_suffix[i+1]
        total = left_distinct + right_distinct
        if total > max_sum:
            max_sum = total
    
    print(max_sum)

if __name__ == "__main__":
    solve()
