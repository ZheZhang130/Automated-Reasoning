import sys
from bisect import bisect_left

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0])
    a = list(map(int, data[1:]))
    
    # Since A is sorted, for each bottom mochi A[i], we need to count
    # how many top mochi A[j] (j != i) satisfy A[j] <= A[i] / 2.
    # Since A[j] must be positive and A[i] >= 1, A[j] <= A[i]/2 implies A[j] < A[i],
    # so j must be less than i. We only need to count j < i such that A[j] <= A[i] / 2.
    
    # For each i, find the largest index j < i such that A[j] <= A[i] / 2.
    # Then the number of valid tops for this bottom is j + 1 (indices 0 to j).
    
    # We can use bisect_left to find the first index where A[idx] > A[i] / 2.
    # Then all indices before that are <= A[i] / 2.
    
    count = 0
    for i in range(n):
        limit = a[i] // 2
        if limit == 0:
            continue
        # Find first index where A[idx] > limit
        idx = bisect_left(a, limit + 1)
        # All indices from 0 to idx-1 have A[k] <= limit
        # Since we need j < i, and idx is the first index > limit,
        # we need to ensure we don't count indices >= i.
        # But since A is sorted and limit = A[i]//2 < A[i] (for A[i] >= 1),
        # all elements <= limit must be at indices < i.
        # So idx will always be <= i.
        # Actually, if there are duplicates, idx could be less than i.
        # The number of valid tops is idx (indices 0 to idx-1).
        count += idx
    
    print(count)

if __name__ == "__main__":
    solve()
