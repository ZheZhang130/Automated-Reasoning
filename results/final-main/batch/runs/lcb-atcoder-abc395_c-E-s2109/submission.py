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
    
    # We need to find the shortest contiguous subarray that has a repeated value.
    # A subarray A[i:j] (inclusive i, exclusive j) has a repeated value if there exists
    # some value x such that x appears at least twice in A[i:j].
    #
    # For each value x, let its positions in A be p1, p2, p3, ...
    # The shortest subarray containing two occurrences of x is A[p_k : p_{k+1}+1]
    # which has length p_{k+1} - p_k + 1.
    #
    # So for each value, we compute the minimum distance between consecutive occurrences.
    # Then we take the minimum over all values.
    
    # Track last seen position for each value
    last_pos = {}
    min_len = float('inf')
    
    for i, x in enumerate(A):
        if x in last_pos:
            # Found a previous occurrence
            dist = i - last_pos[x] + 1
            if dist < min_len:
                min_len = dist
            # Update last position to current
            last_pos[x] = i
        else:
            last_pos[x] = i
    
    if min_len == float('inf'):
        print(-1)
    else:
        print(min_len)

if __name__ == "__main__":
    solve()
