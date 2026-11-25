import sys
from collections import defaultdict

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    N = int(data[0])
    A = list(map(int, data[1:]))
    
    # We need to find the shortest contiguous subarray that contains a duplicate value.
    # A subarray A[i:j] (inclusive i, exclusive j) has a duplicate if there exists
    # some value x such that x appears at least twice in A[i:j].
    #
    # For each value x, let its positions in A be p1, p2, p3, ...
    # The shortest subarray containing two occurrences of x is A[p_k : p_{k+1}+1]
    # which has length p_{k+1} - p_k + 1 (inclusive of both endpoints).
    #
    # So for each value, we compute the minimum distance between consecutive occurrences + 1.
    # Then the answer is the minimum of these distances over all values.
    # If no value appears more than once, output -1.
    
    # Group positions by value
    pos_map = defaultdict(list)
    for idx, val in enumerate(A):
        pos_map[val].append(idx)
    
    min_len = float('inf')
    
    for val, positions in pos_map.items():
        if len(positions) < 2:
            continue
        # Compute minimum distance between consecutive occurrences
        for i in range(1, len(positions)):
            dist = positions[i] - positions[i-1] + 1
            if dist < min_len:
                min_len = dist
                # Optimization: if we find length 2, that's the absolute minimum possible
                if min_len == 2:
                    break
        if min_len == 2:
            break
    
    if min_len == float('inf'):
        print(-1)
    else:
        print(min_len)

if __name__ == "__main__":
    solve()
