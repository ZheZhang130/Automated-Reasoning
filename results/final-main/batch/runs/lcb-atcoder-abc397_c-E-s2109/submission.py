import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    N = int(next(iterator))
    A = [int(next(iterator)) for _ in range(N)]

    # Precompute suffix distinct counts
    # We need to know for each position i (1 to N-1), the number of distinct elements in A[i:]
    # We can do this by iterating backwards and maintaining a set or a frequency map.
    # Since values are up to N, we can use a direct array or a dict.
    
    # Let's use a set for the suffix.
    suffix_distinct = [0] * (N + 1)
    seen_suffix = set()
    for i in range(N - 1, -1, -1):
        seen_suffix.add(A[i])
        suffix_distinct[i] = len(seen_suffix)
    
    # Now compute prefix distinct counts on the fly
    prefix_distinct = 0
    seen_prefix = set()
    max_total = 0
    
    # We iterate split point i from 1 to N-1 (1-based index for the first part)
    # In 0-based indexing, the split is after index i-1, so first part is A[0:i]
    # i goes from 1 to N-1 (number of elements in first part)
    for i in range(1, N):
        val = A[i-1]
        if val not in seen_prefix:
            seen_prefix.add(val)
            prefix_distinct += 1
        
        # First part: A[0]...A[i-1] -> count is prefix_distinct
        # Second part: A[i]...A[N-1] -> count is suffix_distinct[i]
        current_total = prefix_distinct + suffix_distinct[i]
        if current_total > max_total:
            max_total = current_total
            
    print(max_total)

if __name__ == "__main__":
    solve()
