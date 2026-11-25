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
    
    # Sort R values
    sorted_R = sorted(queries_by_R.keys())
    
    # Process
    tails = []  # minimum tail for each length (strictly increasing)
    answers = [0] * Q
    
    # We need to process elements incrementally
    current_pos = 0
    for R in sorted_R:
        # Process all elements from current_pos to R-1
        for pos in range(current_pos, R):
            val = A[pos]
            # Find first tail >= val
            idx = bisect_left(tails, val)
            if idx < len(tails):
                tails[idx] = val
            else:
                tails.append(val)
        current_pos = R
        
        # Answer queries for this R
        for X, idx in queries_by_R[R]:
            # Find first tail > X
            pos = bisect_right(tails, X)
            answers[idx] = pos
    
    # Print answers in order
    for ans in answers:
        print(ans)

if __name__ == "__main__":
    solve()
