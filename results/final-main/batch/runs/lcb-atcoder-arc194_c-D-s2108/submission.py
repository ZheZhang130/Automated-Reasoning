import sys

def solve():
    input_data = sys.stdin.read().split()
    it = iter(input_data)
    N = int(next(it))
    A = [int(next(it)) for _ in range(N)]
    B = [int(next(it)) for _ in range(N)]
    C = [int(next(it)) for _ in range(N)]

    # S0: positions where A[i] == 0 and B[i] == 1 (need to flip 0->1)
    # S1: positions where A[i] == 1 and B[i] == 0 (need to flip 1->0)
    # S_keep: positions where A[i] == B[i] (no flip needed)
    
    S0 = []
    S1 = []
    S_keep = []
    
    for i in range(N):
        if A[i] == 0 and B[i] == 1:
            S0.append((C[i], i))
        elif A[i] == 1 and B[i] == 0:
            S1.append((C[i], i))
        else:
            S_keep.append((C[i], i))
    
    # Sort S0 by C[i] descending (larger C first to get smaller p)
    # Sort S1 by C[i] descending (larger C first to get smaller q, i.e., larger p)
    S0.sort(key=lambda x: x[0], reverse=True)
    S1.sort(key=lambda x: x[0], reverse=True)
    
    m = len(S0) + len(S1)
    
    total_cost = 0
    
    # For S_keep: contribute C[i] * m
    for _, i in S_keep:
        total_cost += C[i] * m
    
    # For S0: flip in order, position p ranges from 1 to |S0|
    for p, (_, i) in enumerate(S0, 1):
        total_cost += C[i] * p
    
    # For S1: flip in order, position p ranges from |S0|+1 to m
    # q = m - p + 1 ranges from |S1| down to 1
    for p, (_, i) in enumerate(S1, 1):
        q = len(S0) - p + 1  # This is wrong, let me fix
        # Actually, p ranges from 1 to |S1|, and the contribution is C[i] * (m - (|S0| + p) + 1)
        # = C[i] * (m - |S0| - p + 1) = C[i] * (|S1| - p + 1)
        total_cost += C[i] * (len(S0) + len(S1) - (len(S0) + p) + 1)
    
    print(total_cost)

if __name__ == "__main__":
    solve()
