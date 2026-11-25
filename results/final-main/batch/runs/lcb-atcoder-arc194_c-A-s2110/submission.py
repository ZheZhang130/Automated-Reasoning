import sys

def solve():
    input_data = sys.stdin.read().split()
    idx = 0
    N = int(input_data[idx]); idx += 1
    A = [int(x) for x in input_data[idx:idx+N]]; idx += N
    B = [int(x) for x in input_data[idx:idx+N]]; idx += N
    C = [int(x) for x in input_data[idx:idx+N]]; idx += N

    # Calculate initial sum
    current_sum = sum(a * c for a, c in zip(A, C))
    
    # Positions where A[i] != B[i]
    flips_1_to_0 = [i for i in range(N) if A[i] == 1 and B[i] == 0]
    flips_0_to_1 = [i for i in range(N) if A[i] == 0 and B[i] == 1]
    
    # Do 1->0 flips first, then 0->1 flips
    total_cost = 0
    for i in flips_1_to_0:
        current_sum -= C[i]
        total_cost += current_sum
    for i in flips_0_to_1:
        current_sum += C[i]
        total_cost += current_sum
    
    print(total_cost)

if __name__ == "__main__":
    solve()
