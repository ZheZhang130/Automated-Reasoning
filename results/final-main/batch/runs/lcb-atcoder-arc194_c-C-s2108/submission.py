import sys

def solve():
    data = sys.stdin.read().split()
    it = iter(data)
    N = int(next(it))
    A = [int(next(it)) for _ in range(N)]
    B = [int(next(it)) for _ in range(N)]
    C = [int(next(it)) for _ in range(N)]

    # Calculate initial sum
    S0 = sum(A[i] * C[i] for i in range(N))
    
    # Identify indices where A[i] != B[i]
    # U: indices where A[i]=0, B[i]=1 (need to flip 0->1)
    # V: indices where A[i]=1, B[i]=0 (need to flip 1->0)
    U = []
    V = []
    
    for i in range(N):
        if A[i] == 0 and B[i] == 1:
            U.append(C[i])
        elif A[i] == 1 and B[i] == 0:
            V.append(C[i])
    
    # Sort V descending (heaviest first)
    V.sort(reverse=True)
    # Sort U ascending (lightest first)
    U.sort()
    
    k = len(U) + len(V)
    
    # Total cost = k * S0 + sum over V of (-C[i] * (k - position)) + sum over U of (C[i] * (k - len(V) - position))
    # Position in V: 0 to len(V)-1, coefficient = k - position
    # Position in U: 0 to len(U)-1, coefficient = k - len(V) - position
    
    cost = k * S0
    
    for i, v in enumerate(V):
        cost += -v * (k - i)
    
    for j, u in enumerate(U):
        cost += u * (k - len(V) - j)
    
    print(cost)

if __name__ == '__main__':
    solve()
