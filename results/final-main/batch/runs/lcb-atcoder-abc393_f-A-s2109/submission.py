import sys
from bisect import bisect_right

def solve():
    input_data = sys.stdin.read().split()
    it = iter(input_data)
    
    N = int(next(it))
    Q = int(next(it))
    
    A = [int(next(it)) for _ in range(N)]
    
    # Compress values
    sorted_A = sorted(set(A))
    val_to_idx = {v: i+1 for i, v in enumerate(sorted_A)}
    max_val = len(sorted_A)
    
    # Read queries
    queries = []
    for i in range(Q):
        R = int(next(it))
        X = int(next(it))
        queries.append((R, X, i))
    
    # Sort queries by R
    queries.sort(key=lambda x: x[0])
    
    # BIT for max
    bit = [0] * (max_val + 2)
    
    def update(idx, val):
        while idx <= max_val:
            if bit[idx] < val:
                bit[idx] = val
            idx += idx & (-idx)
    
    def query(idx):
        res = 0
        while idx > 0:
            if bit[idx] > res:
                res = bit[idx]
            idx -= idx & (-idx)
        return res
    
    results = [0] * Q
    q_idx = 0
    num_queries = len(queries)
    
    # Process
    for r in range(N):
        val = A[r]
        idx = val_to_idx[val]
        
        # Find max LIS ending with value < val
        prev_max = query(idx - 1)
        new_len = prev_max + 1
        update(idx, new_len)
        
        # Answer queries with this R (R is 1-indexed, so we use r+1)
        while q_idx < num_queries and queries[q_idx][0] == r + 1:
            _, X, original_idx = queries[q_idx]
            # Find the largest value in sorted_A that is <= X
            pos = bisect_right(sorted_A, X)
            if pos > 0:
                res = query(pos)
            else:
                res = 0
            results[original_idx] = res
            q_idx += 1
    
    # Print results
    for res in results:
        print(res)

solve()
