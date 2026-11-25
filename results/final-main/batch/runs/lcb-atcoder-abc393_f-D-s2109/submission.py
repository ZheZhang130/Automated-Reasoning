import sys
from bisect import bisect_left

def solve():
    input_data = sys.stdin.read().split()
    it = iter(input_data)
    N = int(next(it))
    Q = int(next(it))
    A = [int(next(it)) for _ in range(N)]
    queries = []
    for _ in range(Q):
        R = int(next(it))
        X = int(next(it))
        queries.append((R, X))
    
    # Precompute for each prefix the LIS ending at each value
    # We use a Fenwick tree (BIT) to store max LIS length ending with value <= v
    # But values are up to 1e9, so we need coordinate compression per prefix?
    # Actually, we can process queries offline by sorting by R.
    # For a fixed R, we consider A[0..R-1]. We want max LIS with values <= X.
    # We can maintain a BIT over compressed values.
    
    # Collect all values that appear in A
    all_values = sorted(list(set(A)))
    val_to_idx = {v: i for i, v in enumerate(all_values)}
    M = len(all_values)
    
    # We'll process queries offline, sorted by R
    # For each R, we add A[R-1] to our data structure
    # Then answer queries with this R
    
    # BIT for max LIS
    bit = [0] * (M + 1)
    
    def update(idx, val):
        idx += 1  # 1-indexed
        while idx <= M:
            bit[idx] = max(bit[idx], val)
            idx += idx & (-idx)
    
    def query(idx):
        idx += 1
        res = 0
        while idx > 0:
            res = max(res, bit[idx])
            idx -= idx & (-idx)
        return res
    
    # Sort queries by R
    sorted_queries = sorted(enumerate(queries), key=lambda x: x[1][0])
    
    results = [0] * Q
    current_idx = 0
    
    for rank, (R, X) in sorted_queries:
        # Add elements from current_idx to R-1
        while current_idx < R:
            val = A[current_idx]
            v_idx = val_to_idx[val]
            # LIS ending at this value = 1 + max LIS ending with value < val
            # We query BIT for max value < val, which is query(v_idx - 1)
            prev_max = query(v_idx - 1)
            new_len = prev_max + 1
            update(v_idx, new_len)
            current_idx += 1
        
        # Now query for max LIS with values <= X
        # Find the largest value <= X
        # We need to query the BIT for all values <= X
        # Since BIT stores max over ranges, we can query the BIT at the index of X
        # But we need the index of the largest value <= X
        # We can use bisect_right to find the index in all_values
        import bisect
        idx_in_all = bisect.bisect_right(all_values, X) - 1
        if idx_in_all < 0:
            results[rank] = 0
        else:
            results[rank] = query(idx_in_all)
    
    for r in results:
        print(r)

solve()
