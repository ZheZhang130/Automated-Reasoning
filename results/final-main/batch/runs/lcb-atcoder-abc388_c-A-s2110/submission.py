import sys
from bisect import bisect_left

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    A = list(map(int, input_data[1:]))
    
    # We need to count pairs (i, j) with i < j such that A[i] <= A[j] / 2
    # Since A is sorted, for each j, we want to count i < j where A[i] <= A[j] // 2
    
    # For each j, we need to find how many i < j satisfy A[i] <= A[j] // 2
    # Since A is sorted, we can use binary search to find the largest index i
    # such that A[i] <= A[j] // 2. Then the count is i + 1 (since indices are 0-based)
    # But we must ensure i < j. Since A[i] <= A[j] // 2 and A[j] >= 1, 
    # A[i] <= A[j] // 2 < A[j], so i will always be < j.
    
    total = 0
    for j in range(N):
        limit = A[j] // 2
        if limit == 0:
            continue
        
        # Find the rightmost index where A[i] <= limit
        # bisect_right returns the insertion point after all elements <= limit
        # So the number of elements <= limit is bisect_right(A, limit)
        count = bisect_left(A, limit + 1)  # This gives the count of elements <= limit
        total += count
    
    print(total)

if __name__ == "__main__":
    solve()
