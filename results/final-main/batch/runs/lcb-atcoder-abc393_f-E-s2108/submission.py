import sys
from bisect import bisect_left

def solve():
    input_data = sys.stdin.read().split()
    it = iter(input_data)
    
    N = int(next(it))
    Q = int(next(it))
    
    A = [int(next(it)) for _ in range(N)]
    
    # Precompute prefix LIS for each value
    # For each position i, we want to know: what is the LIS ending at or before i with value <= v?
    # But we need to answer queries offline or online.
    # 
    # Approach:
    # For a query (R, X), we consider A[0..R-1] and values <= X.
    # We want the longest strictly increasing subsequence using only values <= X.
    # 
    # We can precompute for each position i and each value v, the LIS length ending at i with value v.
    # But values are up to 10^9, so we need to compress or use a different approach.
    #
    # Alternative approach:
    # For a fixed R, we want the LIS of A[0..R-1] restricted to values <= X.
    # This is equivalent to: take A[0..R-1], filter values <= X, then find LIS.
    # But we have many queries.
    #
    # Key insight: 
    # The LIS of a sequence can be computed by maintaining an array 'tails' where tails[i] is the smallest ending value of an increasing subsequence of length i+1.
    # For a query (R, X), we want the LIS of A[0..R-1] with values <= X.
    # 
    # We can process queries offline by sorting them by R.
    # As we increase R, we add elements to our data structure.
    # For each element A[i], if A[i] <= X, we can potentially extend a subsequence.
    # 
    # However, the condition is that ALL elements in the subsequence must be <= X.
    # So when we add A[i], if A[i] > X, we ignore it for this query.
    # But different queries have different X.
    #
    # Better approach:
    # For each position i, let's compute the LIS ending at i (considering only elements up to i).
    # Let dp[i] = length of LIS ending at i (using elements from 0 to i).
    # Then for a query (R, X), we want max(dp[i]) for i < R and A[i] <= X, but with the constraint that the entire subsequence has values <= X.
    # 
    # Actually, the standard LIS algorithm maintains tails[j] = smallest ending value of an increasing subsequence of length j+1.
    # For a query (R, X), we want to simulate the LIS algorithm but only considering elements <= X.
    # 
    # We can do this offline:
    # Sort queries by R.
    # As we iterate R from 1 to N, we add A[R-1] to our data structure.
    # For each query (R, X), we want to know the LIS length using only elements <= X from A[0..R-1].
    # 
    # We can maintain a Fenwick tree or segment tree over the values (after coordinate compression).
    # The segment tree will store at each value v: the maximum LIS length ending with a value <= v.
    # But we need to be careful: when we add a new element A[i], we want to update the LIS information.
    # 
    # Standard LIS with coordinate compression:
    # Let's compress the values that appear in A.
    # For each position i, we compute the LIS ending at i: 
    #   len = 1 + max(LIS ending at j < i with A[j] < A[i])
    # But we only care about elements <= X for the query.
    #
    # Revised plan:
    # We'll process queries offline by R.
    # We maintain a data structure that, for each value v, stores the maximum LIS length ending with a value <= v.
    # When we add a new element A[i], we compute its LIS length considering only previous elements.
    # But we need to consider only elements <= X for the query.
    #
    # Actually, let's think differently:
    # For a query (R, X), we want the LIS of the sequence A[0..R-1] restricted to values <= X.
    # This is equivalent to: take the sequence B = [A[i] for i in 0..R-1 if A[i] <= X], then find LIS of B.
    # 
    # We can use a segment tree over the compressed values.
    # The segment tree will store at each node the maximum LIS length in that value range.
    # When we add an element A[i], we update the segment tree.
    # For a query (R, X), we query the segment tree for the range [min_val, X].
    #
    # Steps:
    # 1. Coordinate compress all values in A.
    # 2. Sort queries by R.
    # 3. Iterate R from 1 to N, adding A[R-1] to the data structure.
    # 4. For each query with current R, query the data structure for the range [min_val, X].
    #
    # How to update:
    # When we add A[i], we want to compute the LIS ending at A[i] considering only previous elements.
    # But we need to consider only elements <= X for the query. However, the query X varies.
    #
    # Actually, the standard way is:
    # Maintain a segment tree where at position v (compressed value), we store the maximum LIS length ending with a value <= v.
    # When we add A[i], we compute:
    #   current_len = 1 + query_segment_tree(0, A[i]-1)
    #   update_segment_tree(A[i], current_len)
    # But this is for the standard LIS. For our problem, we need to restrict to values <= X.
    #
    # Correction:
    # The segment tree should store: at position v, the maximum LIS length ending with a value exactly v.
    # Then for a query (R, X), we want the maximum LIS length in the range [min_val, X].
    # But we also need to ensure that the LIS is strictly increasing and uses only values <= X.
    #
    # Actually, the standard LIS algorithm with a segment tree:
    # - The segment tree stores at each leaf v: the maximum LIS length ending with value v.
    # - When adding A[i], we compute: len = 1 + max(segment_tree.query(0, A[i]-1))
    # - Then update segment_tree at A[i] with len.
    # - For a query (R, X), we want max(segment_tree.query(min_val, X)).
    #
    # But there's a catch: the standard LIS algorithm updates the segment tree with the new LIS length ending at A[i].
    # However, if we have multiple elements with the same value, we need to handle them carefully.
    # Since we want strictly increasing, if we have two elements with the same value, only the later one can extend a subsequence ending with a smaller value.
    # But the earlier one might have been used in a subsequence.
    #
    # Actually, for strictly increasing subsequence, if we have duplicate values, we can only use one of them in a subsequence.
    # The standard approach is to update the segment tree at position A[i] with the new LIS length, but we should take the maximum.
    # However, if we have multiple elements with the same value, we want to keep the one that gives the longest LIS.
    # But note: if we have two elements with the same value, say at indices i and j (i < j), then when we process j, 
    # we can extend a subsequence that ended at i? No, because it's strictly increasing, so we cannot use both.
    # Actually, we can only use one of them. So when we update, we should update with the new LIS length, but we don't need to worry about duplicates for the same value because the segment tree will store the maximum LIS length ending with that value.
    #
    # However, the issue is: when we add a new element A[i], we compute the LIS length ending at i by querying the segment tree for values < A[i].
    # Then we update the segment tree at A[i] with this new length. But if there was already an element with value A[i] at an earlier position, 
    # we should update the segment tree at A[i] with the new length only if it's greater. But actually, we want to store the maximum LIS length ending with value A[i] seen so far.
    # However, for strictly increasing, if we have two elements with the same value, the later one can extend a subsequence that ended with a value less than A[i], but it cannot extend a subsequence that ended with A[i] (because it must be strictly increasing).
    # So the update is: new_len = 1 + query(0, A[i]-1)
    # Then update(A[i], new_len) -> but we should take max(current_value_at_A[i], new_len).
    #
    # But wait: the standard LIS algorithm with a Fenwick tree or segment tree does exactly this.
    # However, for the query, we want the maximum LIS length in the range [min_val, X].
    # But note: the segment tree stores the maximum LIS length ending at each value. Then the answer for a query (R, X) is the maximum value in the segment tree for values in [min_val, X].
    #
    # However, there's a problem: the segment tree is built as we add elements. But the LIS length stored at a value v is the maximum LIS length ending with value v using elements up to the current R.
    # And for a query (R, X), we want the maximum LIS length using elements up to R and with values <= X.
    # This is exactly max(segment_tree.query(min_val, X)).
    #
    # Steps:
    # 1. Coordinate compress all values in A to the range [0, distinct_count-1].
    # 2. Sort queries by R.
    # 3. Initialize a segment tree (or Fenwick tree) that supports:
    #      - update(pos, value): set tree[pos] = max(tree[pos], value)
    #      - query(l, r): return max(tree[l..r])
    # 4. Iterate R from 1 to N:
    #      - Let v = compressed_value(A[R-1])
    #      - current_len = 1 + query(0, v-1)   [if v>0, else 1]
    #      - update(v, current_len)
    #      - For all queries with this R, answer = query(0, compressed_value(X))
    #
    # But note: the query X might not be in the compressed values. So we need to compress X as well? 
    # Actually, we can compress all values that appear in A and also the X values? 
    # But X can be up to 10^9, and we only care about values that appear in A.
    # So we compress only the values in A. Then for a query X, we find the largest compressed value that is <= X.
    #
    # Implementation:
    # - Collect all values in A and sort them to get the mapping.
    # - For a value X in a query, we can use bisect_right to find the index in the sorted unique values of A that is <= X.
    #
    # Let's code accordingly.

import sys
from bisect import bisect_right

# Increase recursion depth just in case, though we won't use recursion.
sys.setrecursionlimit(200000)

def main():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    
    N = int(next(iterator))
    Q = int(next(iterator))
    
    A = [int(next(iterator)) for _ in range(N)]
    
    queries = []
    for i in range(Q):
        R = int(next(iterator))
        X = int(next(iterator))
        queries.append((R, X, i))
    
    # Coordinate compression for values in A
    sorted_unique_A = sorted(set(A))
    val_to_rank = {v: i for i, v in enumerate(sorted_unique_A)}
    num_vals = len(sorted_unique_A)
    
    # Build a segment tree (using an array) for range max query and point update.
    # We'll use a simple array-based segment tree.
    # Size: 4 * num_vals
    tree = [0] * (4 * num_vals)
    
    def update(node, start, end, idx, value):
        if start == end:
            tree[node] = max(tree[node], value)
            return
        mid = (start + end) // 2
        if idx <= mid:
            update(2*node, start, mid, idx, value)
        else:
            update(2*node+1, mid+1, end, idx, value)
        tree[node] = max(tree[2*node], tree[2*node+1])
    
    def query(node, start, end, l, r):
        if r < start or end < l:
            return 0
        if l <= start and end <= r:
            return tree[node]
        mid = (start + end) // 2
        left_max = query(2*node, start, mid, l, r)
        right_max = query(2*node+1, mid+1, end, l, r)
        return max(left_max, right_max)
    
    # Sort queries by R
    queries.sort(key=lambda x: x[0])
    
    results = [0] * Q
    current_R = 0
    
    # We'll iterate through the sorted queries and also through A
    # But note: queries are sorted by R, so we can process A up to R for each query.
    
    idx_queries = 0
    num_queries = len(queries)
    
    while idx_queries < num_queries:
        R, X, original_idx = queries[idx_queries]
        
        # Process A from current_R to R-1
        while current_R < R:
            val = A[current_R]
            rank = val_to_rank[val]
            
            # Query the segment tree for max in [0, rank-1]
            if rank > 0:
                current_len = 1 + query(1, 0, num_vals-1, 0, rank-1)
            else:
                current_len = 1
            
            # Update the segment tree at rank with current_len
            update(1, 0, num_vals-1, rank, current_len)
            
            current_R += 1
        
        # Now answer the query
        # We need the max in [0, rank_X] where rank_X is the largest rank such that sorted_unique_A[rank_X] <= X
        # Find the largest index in sorted_unique_A that is <= X
        rank_X = bisect_right(sorted_unique_A, X) - 1
        if rank_X < 0:
            # No value <= X, so answer is 0? But the problem guarantees X >= min(A[0..R-1]), so there is at least one value <= X.
            # So rank_X should be >= 0.
            results[original_idx] = 0
        else:
            ans = query(1, 0, num_vals-1, 0, rank_X)
            results[original_idx] = ans
        
        idx_queries += 1
    
    # Print results in the original order
    for res in results:
        print(res)

if __name__ == '__main__':
    main()
