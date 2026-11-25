import sys
from typing import List

def solve() -> None:
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    it = iter(input_data)
    N = int(next(it))
    M = int(next(it))
    
    B = []
    for _ in range(N):
        B.append(int(next(it)))
    
    W = []
    for _ in range(M):
        W.append(int(next(it)))
    
    # Sort both arrays in descending order
    B.sort(reverse=True)
    W.sort(reverse=True)
    
    # We need to choose k black balls and k white balls for some k >= 0
    # Or choose k black balls and j white balls where k >= j
    # To maximize sum, we should always pick the largest available balls
    # 
    # Strategy:
    # Consider picking exactly k black balls and k white balls (k from 0 to min(N, M))
    # Then we can also pick additional black balls (since we can have more black than white)
    # 
    # Let's compute prefix sums for B and W
    # prefix_B[k] = sum of top k black balls
    # prefix_W[k] = sum of top k white balls
    # 
    # For a fixed k (number of white balls to pick), we pick k black balls and k white balls
    # Then we can pick any number of additional black balls (from the remaining ones)
    # that have positive value.
    # 
    # So for each k from 0 to min(N, M):
    #   base_sum = prefix_B[k] + prefix_W[k]
    #   additional = sum of positive values in B[k:]
    #   total = base_sum + additional
    # 
    # We want max over all k
    
    # Compute prefix sums
    prefix_B = [0] * (N + 1)
    for i in range(N):
        prefix_B[i+1] = prefix_B[i] + B[i]
    
    prefix_W = [0] * (M + 1)
    for i in range(M):
        prefix_W[i+1] = prefix_W[i] + W[i]
    
    # Compute suffix sums of positive values for B
    # suffix_pos_B[i] = sum of positive values in B[i:]
    suffix_pos_B = [0] * (N + 1)
    for i in range(N-1, -1, -1):
        suffix_pos_B[i] = suffix_pos_B[i+1] + (B[i] if B[i] > 0 else 0)
    
    max_sum = 0  # We can always choose 0 balls
    
    for k in range(min(N, M) + 1):
        current_sum = prefix_B[k] + prefix_W[k] + suffix_pos_B[k]
        if current_sum > max_sum:
            max_sum = current_sum
    
    print(max_sum)

if __name__ == "__main__":
    solve()
