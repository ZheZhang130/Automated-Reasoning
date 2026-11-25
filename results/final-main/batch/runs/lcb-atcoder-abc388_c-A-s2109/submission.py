import sys
from bisect import bisect_right

def solve():
    input_data = sys.stdin.read().split()
    N = int(input_data[0])
    A = list(map(int, input_data[1:N+1]))
    
    # We need to count pairs (i, j) with i != j such that A[i] <= A[j] / 2
    # Since A is sorted, for each j, we count elements <= A[j] / 2
    # But we must exclude j itself if A[j] <= A[j] / 2 (which is impossible for A[j] >= 1)
    # Actually, the condition is A[i] <= A[j] / 2, which means A[i] < A[j] for A[j] >= 1
    # So i != j is automatically satisfied.
    
    # However, we need to be careful: bisect_right gives us the count of elements <= limit
    # But we need to exclude the case where the element at index j itself is counted
    # if A[j] <= A[j] / 2. But since A[j] >= 1, A[j] > A[j] / 2, so A[j] is never <= A[j] / 2.
    # So we don't need to exclude anything.
    
    # Wait, let me re-check: if A[j] = 2, then A[j] / 2 = 1. Elements <= 1 are counted.
    # A[j] = 2 is not <= 1, so it's not counted. Good.
    
    # But what if there are duplicate values? For example, A = [2, 2, 4, 4, 7, 10]
    # For j=0 (A[0]=2), limit=1, count=0
    # For j=1 (A[1]=2), limit=1, count=0
    # For j=2 (A[2]=4), limit=2, count=2 (both 2s)
    # For j=3 (A[3]=4), limit=2, count=2 (both 2s)
    # For j=4 (A[4]=7), limit=3, count=2 (both 2s)
    # For j=5 (A[5]=10), limit=5, count=4 (2, 3, 4, 4)
    # Total = 0+0+2+2+2+4 = 10, but expected is 8.
    
    # The issue is that we're counting pairs where the top mochi is at index i and bottom at index j,
    # but we're not distinguishing between different mochi of the same size.
    # Actually, the problem says "Two kagamimochi are distinguished if at least one of the mochi is different,
    # even if the sizes of the mochi are the same."
    # This means we need to count pairs of indices (i, j) with i != j such that A[i] <= A[j] / 2.
    
    # So my approach is correct, but let me re-check the sample.
    # Sample 1: A = [2, 3, 4, 4, 7, 10]
    # Pairs:
    # (0, 2): 2 <= 4/2 = 2 ✓
    # (0, 3): 2 <= 4/2 = 2 ✓
    # (1, 2): 3 <= 4/2 = 2 ✗
    # (1, 3): 3 <= 4/2 = 2 ✗
    # (0, 5): 2 <= 10/2 = 5 ✓
    # (1, 5): 3 <= 10/2 = 5 ✓
    # (2, 5): 4 <= 10/2 = 5 ✓
    # (3, 5): 4 <= 10/2 = 5 ✓
    # That's 8 pairs. Let me trace through my code again.
    
    # For j=0 (A[0]=2), limit=1, bisect_right([2,3,4,4,7,10], 1) = 0
    # For j=1 (A[1]=3), limit=1, bisect_right([2,3,4,4,7,10], 1) = 0
    # For j=2 (A[2]=4), limit=2, bisect_right([2,3,4,4,7,10], 2) = 1 (only the first 2)
    # For j=3 (A[3]=4), limit=2, bisect_right([2,3,4,4,7,10], 2) = 1
    # For j=4 (A[4]=7), limit=3, bisect_right([2,3,4,4,7,10], 3) = 2 (2 and 3)
    # For j=5 (A[5]=10), limit=5, bisect_right([2,3,4,4,7,10], 5) = 4 (2, 3, 4, 4)
    # Total = 0+0+1+1+2+4 = 8. That's correct!
    
    # The issue with my previous code was using bisect_left instead of bisect_right.
    # bisect_left returns the first index where the element could be inserted while maintaining order,
    # which gives the count of elements < limit.
    # bisect_right returns the first index where the element could be inserted after all elements <= limit,
    # which gives the count of elements <= limit.
    
    count = 0
    for j in range(N):
        val = A[j]
        limit = val // 2
        idx = bisect_right(A, limit)
        count += idx
    
    print(count)

if __name__ == "__main__":
    solve()
