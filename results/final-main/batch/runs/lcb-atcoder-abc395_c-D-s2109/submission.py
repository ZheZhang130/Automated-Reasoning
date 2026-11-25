import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    A = list(map(int, input_data[1:]))
    
    if N == 0:
        print(-1)
        return
    
    # Track the last seen position for each value
    last_pos = {}
    min_len = float('inf')
    
    for i, val in enumerate(A):
        if val in last_pos:
            # Found a previous occurrence
            prev = last_pos[val]
            # The shortest subarray containing both is from prev to i
            length = i - prev + 1
            if length < min_len:
                min_len = length
        last_pos[val] = i
    
    if min_len == float('inf'):
        print(-1)
    else:
        print(min_len)

if __name__ == "__main__":
    solve()
