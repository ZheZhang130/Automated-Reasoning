import sys
from sys import stdin

def solve():
    input_data = stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    N = int(next(iterator))
    A = [int(next(iterator)) for _ in range(N)]
    
    # Right frequency array (values are 1..N)
    right_freq = [0] * (N + 1)
    for x in A:
        right_freq[x] += 1
    
    # Right distinct count
    right_distinct = sum(1 for f in right_freq if f > 0)
    
    # Left seen flags
    left_seen = [False] * (N + 1)
    left_distinct = 0
    
    max_sum = 0
    
    # Iterate split point i from 1 to N-1 (left subarray has length i)
    for i in range(N - 1):
        x = A[i]
        
        # Move x from right to left
        if not left_seen[x]:
            left_seen[x] = True
            left_distinct += 1
        
        right_freq[x] -= 1
        if right_freq[x] == 0:
            right_distinct -= 1
        
        current_sum = left_distinct + right_distinct
        if current_sum > max_sum:
            max_sum = current_sum
    
    print(max_sum)

if __name__ == "__main__":
    solve()
