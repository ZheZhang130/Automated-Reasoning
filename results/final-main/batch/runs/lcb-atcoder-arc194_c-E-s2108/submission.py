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
    
    # Positions where A[i] == 1, B[i] == 1 (shared 1s that can be temporarily flipped)
    shared_ones = []
    # Positions where A[i] == 1, B[i] == 0 (need to flip 1->0)
    n10 = []
    # Positions where A[i] == 0, B[i] == 1 (need to flip 0->1)
    n01 = []
    
    for i in range(N):
        if A[i] == 1 and B[i] == 1:
            shared_ones.append(C[i])
        elif A[i] == 1 and B[i] == 0:
            n10.append(C[i])
        elif A[i] == 0 and B[i] == 1:
            n01.append(C[i])
    
    # Sort shared_ones in descending order
    shared_ones.sort(reverse=True)
    # Sort n10 in descending order
    n10.sort(reverse=True)
    # Sort n01 in ascending order
    n01.sort()
    
    # Calculate initial sum of A[k] * C[k]
    initial_S = sum(a * c for a, c in zip(A, C))
    
    # Calculate the cost for each possible number of shared_ones to temporarily flip
    best_cost = float('inf')
    
    for k in range(len(shared_ones) + 1):
        # Calculate cost for flipping k shared_ones
        current_S = initial_S
        
        # Cost for flipping k shared_ones
        cost = 0
        for i in range(k):
            current_S -= shared_ones[i]
            cost += current_S
        
        # Cost for flipping n10
        for c in n10:
            current_S -= c
            cost += current_S
        
        # Cost for flipping n01
        for c in n01:
            current_S += c
            cost += current_S
        
        best_cost = min(best_cost, cost)
    
    print(best_cost)

solve()
