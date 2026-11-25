import sys
from bisect import bisect_left, bisect_right

def solve():
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
    
    # Group queries by R
    queries_by_R = {}
    for R, X, idx in queries:
        if R not in queries_by_R:
            queries_by_R[R] = []
        queries_by_R[R].append((X, idx))
    
    # Sort R values to process in order
    sorted_R = sorted(queries_by_R.keys())
    
    # tails[i] = smallest ending element of an increasing subsequence of length i+1
    tails = []
    
    answers = [0] * Q
    
    for R in sorted_R:
        # Process elements up to index R-1 (since R is 1-based)
        # We need to update tails with A[0]...A[R-1]
        # But we already processed up to previous R, so we continue from there
        # Actually, we need to process all elements from 0 to R-1
        # Since we process R in increasing order, we can just continue appending
        
        # But wait, we need to process elements one by one.
        # Let's restructure: we'll process elements as we go.
        pass
    
    # Better approach: process elements one by one and answer queries when we reach R
    # Reset and do it properly
    
    tails = []
    query_idx = 0
    
    # We need to process elements and answer queries at specific R
    # Let's create a list of (R, X, original_index) and sort by R
    query_list = []
    for i in range(Q):
        R, X = queries[i][0], queries[i][1]
        query_list.append((R, X, i))
    
    query_list.sort(key=lambda x: x[0])
    
    # Now process
    tails = []
    query_ptr = 0
    
    for R, X, original_idx in query_list:
        # Process elements from current position up to R-1
        # But we don't track current position. Let's track it.
        pass
    
    # Let's restart with proper tracking
    tails = []
    query_ptr = 0
    current_pos = 0
    
    # We need to process queries in order of R
    # For each query, we need to have processed all elements up to R-1
    
    # Actually, let's just iterate through all elements and answer queries when we reach R
    # But queries are given in arbitrary order, so we need to store them
    
    # Let's use a different approach:
    # 1. Group queries by R
    # 2. Process elements one by one
    # 3. When we reach position R, answer all queries with that R
    
    queries_by_R = {}
    for i in range(Q):
        R, X = queries[i][0], queries[i][1]
        if R not in queries_by_R:
            queries_by_R[R] = []
        queries_by_R[R].append((X, i))
    
    # Sort R values
    sorted_R = sorted(queries_by_R.keys())
    
    tails = []
    current_pos = 0
    
    for R in sorted_R:
        # Process elements from current_pos to R-1
        for i in range(current_pos, R):
            val = A[i]
            # Find the first tail >= val
            idx = bisect_left(tails, val)
            if idx < len(tails):
                tails[idx] = val
            else:
                tails.append(val)
        
        current_pos = R
        
        # Answer queries for this R
        for X, original_idx in queries_by_R[R]:
            # Find the first tail > X
            idx = bisect_right(tails, X)
            answers[original_idx] = idx
    
    # Print answers
    for ans in answers:
        print(ans)

if __name__ == "__main__":
    solve()
