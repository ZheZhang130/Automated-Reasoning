import sys
from bisect import bisect_left

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0])
    a = list(map(int, data[1:]))
    
    count = 0
    # For each mochi i (as top), we need to find how many mochi j (as bottom)
    # satisfy: a[i] <= a[j] / 2  =>  a[j] >= 2 * a[i]
    # Since array is sorted, we can use binary search to find the first index
    # where a[j] >= 2 * a[i], then all indices from there to end are valid.
    
    for i in range(n):
        val = a[i]
        target = 2 * val
        # Find first index j where a[j] >= target
        idx = bisect_left(a, target)
        if idx < n:
            count += (n - idx)
    
    print(count)

if __name__ == "__main__":
    solve()
