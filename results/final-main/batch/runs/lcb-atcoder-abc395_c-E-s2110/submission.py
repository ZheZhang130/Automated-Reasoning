import sys
from collections import defaultdict

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    N = int(data[0])
    A = list(map(int, data[1:]))
    
    # We need to find the shortest contiguous subarray that has a repeated value.
    # A subarray A[i:j] (inclusive i, exclusive j) has a repeated value if there exists
    # some value x such that x appears at least twice in A[i:j].
    #
    # For each value x, let its positions in A be p1, p2, p3, ...
    # The shortest subarray containing two occurrences of x is from p_k to p_{k+1} (inclusive),
    # which has length = p_{k+1} - p_k + 1.
    #
    # So we just need to:
    # 1. Group positions by value.
    # 2. For each value, compute the minimum difference between consecutive positions.
    # 3. The answer is the minimum of these differences + 1.
    # 4. If no value appears more than once, output -1.
    
    pos = defaultdict(list)
    for idx, val in enumerate(A):
        pos[val].append(idx)
    
    min_len = float('inf')
    
    for val, positions in pos.items():
        if len(positions) < 2:
            continue
        for i in range(len(positions) - 1):
            diff = positions[i+1] - positions[i]
            if diff + 1 < min_len:
                min_len = diff + 1
    
    if min_len == float('inf'):
        print(-1)
    else:
        print(min_len)

if __name__ == "__main__":
    solve()
