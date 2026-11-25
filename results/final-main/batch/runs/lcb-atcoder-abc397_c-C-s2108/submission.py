import sys
from sys import stdin

def solve():
    input_data = stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    N = int(next(iterator))
    A = [int(next(iterator)) for _ in range(N)]

    # Count frequencies for the right subarray (initially the whole array)
    freq = [0] * (N + 1)
    for x in A:
        freq[x] += 1

    # Count distinct elements in the right subarray
    right_distinct = sum(1 for x in range(1, N + 1) if freq[x] > 0)

    # Track distinct elements in the left subarray
    left_distinct = 0
    seen_left = [False] * (N + 1)

    max_sum = 0

    # Iterate through split positions: left subarray is A[0:i], right is A[i:N]
    # i ranges from 1 to N-1 (inclusive)
    for i in range(N - 1):
        x = A[i]
        
        # Move x from right to left
        if not seen_left[x]:
            seen_left[x] = True
            left_distinct += 1
        
        freq[x] -= 1
        if freq[x] == 0:
            right_distinct -= 1
        
        current_sum = left_distinct + right_distinct
        if current_sum > max_sum:
            max_sum = current_sum

    print(max_sum)

if __name__ == "__main__":
    solve()
