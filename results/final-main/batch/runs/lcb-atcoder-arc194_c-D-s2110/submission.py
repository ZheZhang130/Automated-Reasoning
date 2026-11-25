import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    
    N = int(next(iterator))
    A = [int(next(iterator)) for _ in range(N)]
    B = [int(next(iterator)) for _ in range(N)]
    C = [int(next(iterator)) for _ in range(N)]
    
    # Calculate S1 = sum of C[k] for all k where A[k] == 1
    S1 = sum(C[i] for i in range(N) if A[i] == 1)
    
    # Separate positions into three categories:
    # 1. A[i] == 0, B[i] == 1: need to flip 0->1
    # 2. A[i] == 1, B[i] == 0: need to flip 1->0
    # 3. A[i] == B[i]: no flip needed (but we might flip if it helps)
    
    ones_to_flip = []  # positions where A[i] == 1, B[i] == 0 (1->0)
    zeros_to_flip = []  # positions where A[i] == 0, B[i] == 1 (0->1)
    
    for i in range(N):
        if A[i] == 1 and B[i] == 0:
            ones_to_flip.append((C[i], i))
        elif A[i] == 0 and B[i] == 1:
            zeros_to_flip.append((C[i], i))
    
    # Sort ones_to_flip by C[i] in descending order (to reduce S1 faster)
    # Sort zeros_to_flip by C[i] in ascending order (to increase S1 slower)
    ones_to_flip.sort(key=lambda x: x[0], reverse=True)
    zeros_to_flip.sort(key=lambda x: x[0])
    
    # Calculate total cost
    total_cost = 0
    current_S1 = S1
    
    # Do all 1->0 flips first
    for c, i in ones_to_flip:
        current_S1 -= c
        total_cost += current_S1
    
    # Do all 0->1 flips
    for c, i in zeros_to_flip:
        current_S1 += c
        total_cost += current_S1
    
    print(total_cost)

if __name__ == "__main__":
    solve()
