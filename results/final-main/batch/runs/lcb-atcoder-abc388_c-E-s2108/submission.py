import sys
from bisect import bisect_right

def solve():
    input = sys.stdin.read
    data = input().split()
    N = int(data[0])
    A = list(map(int, data[1:]))
    
    # A is sorted in ascending order
    # We need to count pairs (i, j) with i != j such that A[i] <= A[j] / 2
    # Since A is sorted, for each j, we want to count i such that A[i] <= A[j] // 2
    # Note: The problem says "Two kagamimochi are distinguished if at least one of the mochi is different"
    # This means we count pairs of indices (i, j) where i != j and A[i] <= A[j] / 2
    
    # For each j, we find how many i satisfy A[i] <= A[j] // 2
    # Since A is sorted, we can use bisect_right to find the count of elements <= half
    # bisect_right returns the first index where A[i] > half, so all indices from 0 to idx-1 have A[i] <= half
    
    count = 0
    for j in range(N):
        val = A[j]
        half = val // 2
        
        if half == 0:
            continue
        
        # Find the number of elements <= half
        idx = bisect_right(A, half)
        
        # Since A[j] >= half (because half = A[j] // 2 and A[j] >= 1),
        # j is always >= idx, so we don't need to subtract anything.
        # Actually, let's verify: if A[j] = 4, half = 2, bisect_right([2,3,4,4,7,10], 2) = 1
        # So index 0 has value 2 which is <= 2. Index 1 has value 3 which is > 2.
        # So idx = 1 means indices 0 to 0 (1 element) satisfy the condition.
        # And j=3 (0-indexed) has A[3]=4, which is not in the range [0, idx-1] = [0, 0].
        # So we don't need to subtract.
        
        count += idx
    
    print(count)

if __name__ == "__main__":
    solve()
