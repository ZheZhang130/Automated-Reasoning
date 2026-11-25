import sys
from bisect import bisect_left, bisect_right

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    
    try:
        N = int(next(iterator))
        Q = int(next(iterator))
        A = [int(next(iterator)) for _ in range(N)]
        queries = []
        for _ in range(Q):
            R = int(next(iterator))
            X = int(next(iterator))
            queries.append((R, X))
    except StopIteration:
        return

    # Precompute for each position i (0-based), the list of values in A[0..i]
    # We want to answer: for prefix R (1-based), so indices 0..R-1,
    # find max length of strictly increasing subsequence with values <= X.
    
    # Idea:
    # For a fixed prefix and threshold X, we want to pick a strictly increasing
    # subsequence using only values <= X.
    # 
    # We can precompute for each index i, the "best" strictly increasing subsequence
    # ending at or before i with values <= some threshold.
    # 
    # However, a more efficient approach:
    # For each value v, we can store the list of indices where v appears in the prefix.
    # But values can be up to 10^9, so we need coordinate compression or a different approach.
    #
    # Alternative approach:
    # For each position i, let dp[i] = the length of the longest strictly increasing
    # subsequence ending at index i (using only values <= A[i]).
    # Then for a query (R, X), we want max(dp[i]) for i in [0, R-1] such that A[i] <= X.
    #
    # But computing dp[i] for all i is O(N^2) naively. We need O(N log N) or similar.
    #
    # We can use a Fenwick tree (or segment tree) over the values (after coordinate compression)
    # to compute dp[i] in O(log N) for each i.
    #
    # Steps:
    # 1. Coordinate compress the values of A to range [1, N] (since only relative order matters).
    # 2. Build a Fenwick tree that supports:
    #      - update(pos, val): set value at pos to max(current, val)
    #      - query(pos): get max value in range [1, pos]
    # 3. For each i from 0 to N-1:
    #      - compressed_val = rank of A[i]
    #      - dp[i] = query(compressed_val - 1) + 1
    #      - update(compressed_val, dp[i])
    # 4. After computing all dp[i], we need to answer queries (R, X).
    #    We want max(dp[i]) for i in [0, R-1] and A[i] <= X.
    #
    # To answer queries efficiently, we can store for each compressed value v,
    # a list of (index, dp_value) pairs, and then for a query (R, X),
    # we consider all v <= X, and for each such v, we want the max dp_value among
    # indices <= R-1.
    #
    # We can precompute for each compressed value v, a sorted list of (index, dp_value)
    # and then use a segment tree or Fenwick tree over the compressed values to store
    # the max dp_value for indices <= R. But R varies per query.
    #
    # Better: For each compressed value v, store a list of (index, dp_value) sorted by index.
    # Then for a query (R, X), we consider all v <= X. For each such v, we want the max dp_value
    # among indices <= R-1. We can use binary search (bisect_right) on the index list for each v.
    # But iterating over all v <= X is too slow (O(N) per query).
    #
    # Alternative: Use a 2D data structure? Too complex.
    #
    # Another idea:
    # Instead of storing per value, we can store for each index i, the value A[i] and dp[i].
    # Then we want max(dp[i]) for i in [0, R-1] and A[i] <= X.
    # This is a 2D range maximum query (rectangle [0, R-1] x [1, X]).
    # We can use a 2D segment tree or a Fenwick tree over one dimension and a segment tree over the other.
    # But 2D structures are heavy.
    #
    # Simpler: Since we only need max over a rectangle, and the points are static,
    # we can use a Fenwick tree over the compressed values, where each node stores a list of (index, dp_value)
    # and we want the max dp_value for indices <= R. But that's still complex.
    #
    # Let's try a different approach:
    # For each compressed value v, we have a list of (index, dp_value) sorted by index.
    # We want max over v <= X of (max dp_value for indices <= R-1).
    # 
    # We can precompute for each v, the list of (index, dp_value) and then for each query,
    # we iterate over v <= X? No, too slow.
    #
    # Instead, we can use a Fenwick tree over the compressed values, where each node stores
    # a list of (index, dp_value) and we want the max dp_value for indices <= R.
    # But merging lists is expensive.
    #
    # Alternative: Use a segment tree over the compressed values, where each node stores
    # a list of (index, dp_value) and we want the max dp_value for indices <= R.
    # Still, merging lists is expensive.
    #
    # Let's think differently:
    # We can process queries offline. Sort queries by X.
    # Then as we increase X, we add values with A[i] <= X to a data structure that supports
    # range maximum query over indices [0, R-1].
    #
    # Steps for offline processing:
    # 1. Coordinate compress A to [1, M] where M <= N.
    # 2. Compute dp[i] for each i as described (using a Fenwick tree over compressed values).
    # 3. Store queries sorted by X.
    # 4. Also, group indices by their compressed value.
    # 5. Use a Fenwick tree (or segment tree) over the indices [0, N-1] to support:
    #      - update(i, val): set value at i to max(current, val)
    #      - query(R): get max value in [0, R-1]
    # 6. Sort queries by X. Also, sort the values by their compressed value.
    # 7. Iterate through sorted queries, and for each query (R, X), add all values with compressed value <= X
    #    to the Fenwick tree. But we need to add each value only once? No, we need to consider all occurrences.
    #    Actually, for a fixed X, we want to consider all indices i such that A[i] <= X.
    #    So we can add all such indices to the Fenwick tree, updating the position i with dp[i].
    #    But we need to do this incrementally as X increases.
    #
    # Revised offline approach:
    # 1. Coordinate compress A to [1, M].
    # 2. Compute dp[i] for each i (using a Fenwick tree over compressed values).
    # 3. Create a list of events: for each compressed value v, and for each occurrence at index i,
    #    create an event (v, i, dp[i]).
    # 4. Sort events by v (compressed value).
    # 5. Sort queries by X (but we need to map X to compressed value). Since X can be up to 10^9,
    #    we compress X as well? Actually, we can use bisect to find the compressed value for X.
    #    But note: X is given as a threshold, and we want A[i] <= X.
    #    So we can compress the distinct values of A, and then for a query X, find the largest compressed value <= X.
    # 6. Use a Fenwick tree over indices [0, N-1] to store the max dp[i] for indices that have been "activated".
    #    Initially, the Fenwick tree is all zeros.
    # 7. Iterate through sorted queries (by X). For each query (R, X), find the compressed value limit L such that
    #    all values with compressed value <= L are <= X. Then, activate all events with compressed value <= L that haven't been activated.
    #    But we need to activate events in increasing order of compressed value.
    #    So, we can maintain a pointer to the events list and activate events until the compressed value exceeds X.
    #    For each activated event (v, i, dp[i]), update the Fenwick tree at index i with dp[i].
    # 8. After activating all events with compressed value <= X, query the Fenwick tree for max in [0, R-1].
    #
    # However, note: we must activate events in increasing order of compressed value, but the queries are also sorted by X.
    # Since X is non-decreasing, we can activate events as we go.
    #
    # Steps:
    # 1. Coordinate compress A: 
    #      distinct_vals = sorted(set(A))
    #      comp_map = {v: i+1 for i, v in enumerate(distinct_vals)}  # 1-indexed
    #      M = len(distinct_vals)
    # 2. Compute dp[i] for each i:
    #      Use a Fenwick tree (BIT) over [1, M] to store max dp for each compressed value.
    #      For i in 0..N-1:
    #          v = comp_map[A[i]]
    #          dp[i] = query_BIT(v-1) + 1
    #          update_BIT(v, dp[i])
    # 3. Prepare events: for each i, event = (comp_map[A[i]], i, dp[i])
    # 4. Sort events by compressed value (v).
    # 5. Prepare queries: for each query (R, X), find the compressed value limit L such that 
    #      all values with compressed value <= L are <= X.
    #      We can use bisect_right on distinct_vals to find the index such that distinct_vals[index] <= X.
    #      Then L = index + 1 (if distinct_vals is 0-indexed, then L = index+1 for 1-indexed BIT).
    #      Actually, we want the largest compressed value <= X. 
    #      Let idx = bisect_right(distinct_vals, X) - 1, then L = idx + 1 (if we use 1-indexed for BIT).
    #      But note: if X is less than the smallest value, then L=0, and we activate nothing.
    # 6. Sort queries by X (or by L).
    # 7. Use a BIT over indices [0, N-1] (or [1, N]) to store max dp[i] for activated indices.
    #      Initially, all zeros.
    # 8. Iterate through sorted queries (by X). For each query, activate all events with compressed value <= L.
    #      For each event (v, i, dp[i]), update the BIT at index i with dp[i].
    #      Then query the BIT for max in [0, R-1] (or [1, R] if 1-indexed).
    #
    # Note: The BIT for indices should support point update and range maximum query.
    # Standard BIT for max: 
    #      update(i, val): while i <= N: tree[i] = max(tree[i], val); i += i & -i
    #      query(i): res = 0; while i > 0: res = max(res, tree[i]); i -= i & -i
    #
    # Implementation details:
    #   - Use 1-indexed BIT for both compressed values and indices.
    #   - For the index BIT, we want max over [1, R]. So we update at position i+1 (if 0-indexed i) and query R.
    #
    # Let's code accordingly.

    # Step 1: Coordinate compression for A
    distinct_vals = sorted(set(A))
    comp_map = {v: i+1 for i, v in enumerate(distinct_vals)}  # 1-indexed
    M = len(distinct_vals)

    # Step 2: Compute dp[i] for each i
    # BIT for compressed values (size M)
    bit_comp = [0] * (M + 1)
    
    def update_comp(idx, val):
        while idx <= M:
            bit_comp[idx] = max(bit_comp[idx], val)
            idx += idx & (-idx)
    
    def query_comp(idx):
        res = 0
        while idx > 0:
            res = max(res, bit_comp[idx])
            idx -= idx & (-idx)
        return res

    dp = [0] * N
    for i in range(N):
        v = comp_map[A[i]]
        dp[i] = query_comp(v - 1) + 1
        update_comp(v, dp[i])

    # Step 3: Prepare events
    events = []
    for i in range(N):
        v = comp_map[A[i]]
        events.append((v, i, dp[i]))
    events.sort(key=lambda x: x[0])  # sort by compressed value

    # Step 4: Prepare queries
    # We need to map X to the compressed value limit.
    # For a query (R, X), we want to activate all events with compressed value <= L, where L is the largest compressed value <= X.
    # We can use bisect_right on distinct_vals to find the index such that distinct_vals[index] <= X.
    # Then L = index + 1 (if distinct_vals is 0-indexed, then the compressed value for distinct_vals[index] is index+1).
    # But note: bisect_right returns an insertion point, so distinct_vals[idx-1] <= X < distinct_vals[idx].
    # So the largest compressed value <= X is idx (if we consider 1-indexed, then it's idx).
    # Actually, if distinct_vals = [v1, v2, ..., vM], then comp_map[v] = index+1.
    # bisect_right(distinct_vals, X) returns the first index where distinct_vals[index] > X.
    # So the number of values <= X is idx = bisect_right(distinct_vals, X).
    # Then the compressed value limit L = idx (because comp_map maps to 1..M, and the first idx values are <= X).
    # But note: if X is less than the smallest value, then idx=0, and L=0.
    
    # We'll store queries as (X, R, original_index) and sort by X.
    queries_with_index = []
    for idx, (R, X) in enumerate(queries):
        # Find the number of distinct values <= X
        import bisect
        idx_comp = bisect.bisect_right(distinct_vals, X)  # this is the count of values <= X, and also the compressed value limit (1-indexed)
        queries_with_index.append((X, R, idx_comp, idx))
    
    queries_with_index.sort(key=lambda x: x[0])  # sort by X

    # Step 5: Process queries
    # BIT for indices (size N+1)
    bit_idx = [0] * (N + 1)
    
    def update_idx(i, val):
        # i is 0-indexed, so we use i+1
        pos = i + 1
        while pos <= N:
            bit_idx[pos] = max(bit_idx[pos], val)
            pos += pos & (-pos)
    
    def query_idx(r):
        # query max in [0, r-1] (0-indexed) -> [1, r] in 1-indexed
        pos = r
        res = 0
        while pos > 0:
            res = max(res, bit_idx[pos])
            pos -= pos & (-pos)
        return res

    # Pointer for events
    event_ptr = 0
    results = [0] * Q
    
    for X, R, limit, orig_idx in queries_with_index:
        # Activate all events with compressed value <= limit
        while event_ptr < len(events) and events[event_ptr][0] <= limit:
            v, i, val = events[event_ptr]
            update_idx(i, val)
            event_ptr += 1
        
        # Query the BIT for max in [0, R-1]
        ans = query_idx(R)
        results[orig_idx] = ans

    # Print results
    for ans in results:
        print(ans)

solve()
