import sys
from bisect import bisect_left, bisect_right

def solve():
    input_data = sys.stdin.read().split()
    it = iter(input_data)
    
    N = int(next(it))
    Q = int(next(it))
    
    A = [int(next(it)) for _ in range(N)]
    
    queries = []
    for i in range(Q):
        R = int(next(it))
        X = int(next(it))
        queries.append((R, X, i))
    
    # Group queries by R
    queries_by_R = {}
    for R, X, idx in queries:
        if R not in queries_by_R:
            queries_by_R[R] = []
        queries_by_R[R].append((X, idx))
    
    # Process queries
    answers = [0] * Q
    
    # tails[i] = smallest ending element of an increasing subsequence of length i+1
    tails = []
    
    # Process each position in A
    for i, val in enumerate(A):
        # Find position to replace or append
        pos = bisect_left(tails, val)
        if pos < len(tails):
            tails[pos] = val
        else:
            tails.append(val)
        
        # Answer all queries with R = i+1 (1-indexed)
        if i + 1 in queries_by_R:
            for X, idx in queries_by_R[i + 1]:
                # Find how many tails are <= X
                # Since tails is sorted, we can use bisect_right
                count = bisect_right(tails, X)
                answers[idx] = count
    
    # Print answers in order
    for ans in answers:
        print(ans)

if __name__ == "__main__":
    solve()
