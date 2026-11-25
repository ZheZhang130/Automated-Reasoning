import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    A = [int(x) for x in input_data[1:]]
    
    # Precompute distinct counts from left
    left_distinct = [0] * N
    seen_left = set()
    count = 0
    for i in range(N):
        if A[i] not in seen_left:
            seen_left.add(A[i])
            count += 1
        left_distinct[i] = count
    
    # Precompute distinct counts from right
    right_distinct = [0] * N
    seen_right = set()
    count = 0
    for i in range(N - 1, -1, -1):
        if A[i] not in seen_right:
            seen_right.add(A[i])
            count += 1
        right_distinct[i] = count
    
    # Find maximum sum
    max_sum = 0
    for i in range(N - 1):
        # Split after index i (0-based), so left is A[0..i], right is A[i+1..N-1]
        current_sum = left_distinct[i] + right_distinct[i + 1]
        if current_sum > max_sum:
            max_sum = current_sum
    
    print(max_sum)

if __name__ == "__main__":
    solve()
