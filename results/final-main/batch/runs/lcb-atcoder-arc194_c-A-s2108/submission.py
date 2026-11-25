import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    
    it = iter(data)
    N = int(next(it))
    A = [int(next(it)) for _ in range(N)]
    B = [int(next(it)) for _ in range(N)]
    C = [int(next(it)) for _ in range(N)]
    
    n10 = []  # positions where A[i] = 1, B[i] = 0 (need to flip 1->0)
    n01 = []  # positions where A[i] = 0, B[i] = 1 (need to flip 0->1)
    
    for i in range(N):
        if A[i] == 1 and B[i] == 0:
            n10.append((i, C[i]))
        elif A[i] == 0 and B[i] == 1:
            n01.append((i, C[i]))
    
    # Sort 1->0 positions by C in descending order (flip larger C first)
    n10.sort(key=lambda x: x[1], reverse=True)
    # Sort 0->1 positions by C in ascending order (flip smaller C first)
    n01.sort(key=lambda x: x[1])
    
    # Calculate initial sum of A[k] * C[k]
    initial_S = sum(a * c for a, c in zip(A, C))
    
    # Flip all 1->0 positions first (sorted by C descending)
    total_cost = 0
    for i, c in n10:
        # Flip A[i] from 1 to 0
        # S decreases by C[i]
        initial_S -= c
        total_cost += initial_S
    
    # Flip all 0->1 positions (sorted by C ascending)
    for i, c in n01:
        # Flip A[i] from 0 to 1
        # S increases by C[i]
        initial_S += c
        total_cost += initial_S
    
    print(total_cost)

solve()
