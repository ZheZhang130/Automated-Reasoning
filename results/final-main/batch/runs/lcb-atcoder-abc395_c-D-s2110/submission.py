import sys
from collections import defaultdict

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    N = int(data[0])
    A = list(map(int, data[1:]))
    
    # Dictionary to store the first occurrence index of each value
    first_occurrence = {}
    min_len = float('inf')
    
    for i, x in enumerate(A):
        if x in first_occurrence:
            # Found a duplicate
            prev_idx = first_occurrence[x]
            # The shortest subarray containing both occurrences is from prev_idx to i
            length = i - prev_idx + 1
            if length < min_len:
                min_len = length
        else:
            first_occurrence[x] = i
    
    if min_len == float('inf'):
        print(-1)
    else:
        print(min_len)

if __name__ == "__main__":
    solve()
