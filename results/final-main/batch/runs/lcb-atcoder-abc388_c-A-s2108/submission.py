import sys
from bisect import bisect_right

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    A = list(map(int, input_data[1:]))
    
    # A is sorted in ascending order
    # We need to count pairs (i, j) with i != j such that A[i] <= A[j] / 2
    # For each j, we want to count i such that A[i] <= A[j] // 2
    
    count = 0
    for j in range(N):
        val = A[j]
        half = val // 2
        if half == 0:
            continue
        
        # bisect_right returns the first index where A[i] > half
        # So all indices from 0 to idx-1 have A[i] <= half
        idx = bisect_right(A, half)
        
        count += idx
    
    print(count)

if __name__ == "__main__":
    solve()
