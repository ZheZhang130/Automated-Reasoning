import sys
from bisect import bisect_left

def solve():
    input_data = sys.stdin.read().split()
    it = iter(input_data)
    N = int(next(it))
    X = int(next(it))
    
    # Tables for each vitamin: dp[c] = max vitamin amount with at most c calories
    # Initialize with -1 to indicate unreachable, but 0 is always reachable with 0 calories
    dp = [[0] * (X + 1) for _ in range(3)]
    
    for _ in range(N):
        v = int(next(it))
        a = int(next(it))
        c = int(next(it))
        
        # Update only the table for this vitamin
        # Iterate backwards to avoid using same item multiple times
        for cal in range(X, c - 1, -1):
            dp[v-1][cal] = max(dp[v-1][cal], dp[v-1][cal - c] + a)
    
    # For each vitamin, find the minimum calories needed to achieve at least k units
    # Since dp[v][c] is non-decreasing with c, we can binary search
    # But we need to handle the case where a target is not achievable
    
    def min_cal_for_target(v, target):
        # Find smallest c such that dp[v][c] >= target
        arr = dp[v]
        # Binary search for first index where arr[i] >= target
        lo, hi = 0, X
        ans = X + 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if arr[mid] >= target:
                ans = mid
                hi = mid - 1
            else:
                lo = mid + 1
        return ans
    
    # Find max possible target
    # Upper bound: min of max achievable for each vitamin with full budget X
    max_targets = [min(dp[v][X] for v in range(3)) + 1]
    lo, hi = 0, max_targets[0]
    
    while lo < hi:
        mid = (lo + hi + 1) // 2
        # Check if target mid is achievable
        c1 = min_cal_for_target(0, mid)
        c2 = min_cal_for_target(1, mid)
        c3 = min_cal_for_target(2, mid)
        
        if c1 <= X and c2 <= X and c3 <= X and c1 + c2 + c3 <= X:
            lo = mid
        else:
            hi = mid - 1
    
    print(lo)

if __name__ == "__main__":
    solve()
