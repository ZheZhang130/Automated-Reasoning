import sys
from bisect import bisect_right

def solve():
    input = sys.stdin.read
    data = input().split()
    
    N = int(data[0])
    A = list(map(int, data[1:]))
    
    # For each element A[j] (potential bottom), we want to count how many A[i] 
    # satisfy A[i] <= A[j] / 2.
    # Since A is sorted, we can use bisect_right to find the count of elements <= limit.
    
    count = 0
    for j in range(N):
        val = A[j]
        limit = val // 2
        # Find the number of elements <= limit
        idx = bisect_right(A, limit)
        count += idx
    
    print(count)

if __name__ == "__main__":
    solve()
