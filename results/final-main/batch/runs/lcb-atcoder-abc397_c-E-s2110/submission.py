import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    A = [int(x) for x in input_data[1:]]
    
    # Precompute distinct counts for all possible split points
    # left_distinct[i] = number of distinct elements in A[0:i+1]
    # right_distinct[i] = number of distinct elements in A[i+1:N]
    
    # Compute left_distinct
    left_distinct = [0] * N
    seen_left = set()
    for i in range(N):
        seen_left.add(A[i])
        left_distinct[i] = len(seen_left)
    
    # Compute right_distinct
    # right_distinct[i] is for the subarray starting at i+1
    # So right_distinct[i] corresponds to A[i+1:]
    right_distinct = [0] * N
    seen_right = set()
    for i in range(N - 1, -1, -1):
        seen_right.add(A[i])
        # right_distinct[i] will store count for A[i:]
        # But we need for A[i+1:], so we'll adjust later
        pass
    
    # Let's recompute right_distinct properly
    # right_distinct[i] = distinct count in A[i+1:]
    right_distinct = [0] * N
    seen_right = set()
    for i in range(N - 1, -1, -1):
        seen_right.add(A[i])
        if i == N - 1:
            right_distinct[i] = 0  # This won't be used for any valid split
        else:
            right_distinct[i] = len(seen_right)
    
    # Now compute the answer
    max_sum = 0
    for i in range(N - 1):
        # Split after index i (0-based), so left is A[0:i+1], right is A[i+1:N]
        left_count = left_distinct[i]
        right_count = len(set(A[i+1:]))  # This is O(N) per iteration, too slow
        
    # We need to precompute right_distinct properly
    # right_distinct[i] = distinct count in A[i+1:]
    right_distinct = [0] * N
    seen_right = set()
    for i in range(N - 1, -1, -1):
        seen_right.add(A[i])
        if i == N - 1:
            right_distinct[i] = 0
        else:
            right_distinct[i] = len(seen_right)
    
    # Recompute with correct logic
    right_distinct = [0] * N
    seen_right = set()
    for i in range(N - 1, -1, -1):
        seen_right.add(A[i])
        # right_distinct[i] should be the distinct count in A[i+1:]
        # But we just added A[i], so we need to subtract it
        if i == N - 1:
            right_distinct[i] = 0
        else:
            # After adding A[i], the set contains A[i:]
            # We want A[i+1:], so we need to remove A[i] from consideration
            # But we can't easily remove from set. Instead, let's think differently.
            pass
    
    # Better approach:
    # right_distinct[i] = distinct count in A[i+1:]
    # We can compute this by iterating from right to left and maintaining the set
    # But we need the count BEFORE adding A[i]
    
    right_distinct = [0] * N
    seen_right = set()
    for i in range(N - 1, -1, -1):
        # Before adding A[i], the set contains A[i+1:]
        right_distinct[i] = len(seen_right)
        seen_right.add(A[i])
    
    # Now compute the answer
    max_sum = 0
    for i in range(N - 1):
        left_count = left_distinct[i]
        right_count = right_distinct[i]
        total = left_count + right_count
        if total > max_sum:
            max_sum = total
    
    print(max_sum)

if __name__ == "__main__":
    solve()
