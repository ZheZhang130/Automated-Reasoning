import sys
from collections import defaultdict

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    N = int(data[0])
    A = list(map(int, data[1:]))
    
    # Dictionary to store the last seen index of each value
    last_seen = {}
    min_len = float('inf')
    
    for i in range(N):
        val = A[i]
        if val in last_seen:
            # Found a previous occurrence of the same value
            prev_idx = last_seen[val]
            # The subarray from prev_idx to i (inclusive) has length i - prev_idx + 1
            length = i - prev_idx + 1
            if length < min_len:
                min_len = length
        last_seen[val] = i
    
    if min_len == float('inf'):
        print(-1)
    else:
        print(min_len)

if __name__ == "__main__":
    solve()
