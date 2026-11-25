import sys

def solve():
    data = sys.stdin.read().split()
    it = iter(data)
    N = int(next(it))
    A = [int(next(it)) for _ in range(N)]
    B = [int(next(it)) for _ in range(N)]
    C = [int(next(it)) for _ in range(N)]

    S0 = sum(A[i] * C[i] for i in range(N))

    must_flip = [i for i in range(N) if A[i] != B[i]]
    optional = [i for i in range(N) if A[i] == 1 and B[i] == 1]

    # For must_flip: delta = C[i] if A[i]=0, else -C[i]
    deltas = []
    for i in must_flip:
        if A[i] == 0:
            deltas.append(C[i])
        else:
            deltas.append(-C[i])
    
    # For optional: add both -C[i] and C[i]
    for i in optional:
        deltas.append(-C[i])
        deltas.append(C[i])
    
    deltas.sort()
    
    M = len(deltas)
    total_cost = M * S0
    for idx, d in enumerate(deltas):
        total_cost += d * (M - idx)
    
    print(total_cost)

solve()
