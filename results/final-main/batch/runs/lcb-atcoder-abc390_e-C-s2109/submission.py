import sys
from bisect import bisect_left

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    N = int(next(iterator))
    X = int(next(iterator))
    
    # Tables for each vitamin: dp[v][c] = max vitamin intake with calorie budget c
    # We'll use a list of lists. dp[v] will be a list of size X+1.
    # Initialize with 0.
    dp = [[0] * (X + 1) for _ in range(4)]  # indices 1, 2, 3
    
    for _ in range(N):
        v = int(next(iterator))
        a = int(next(iterator))
        c = int(next(iterator))
        
        # Update knapsack for vitamin v
        # Iterate backwards to avoid using same item twice
        for budget in range(X, c - 1, -1):
            prev = budget - c
            if dp[v][prev] + a > dp[v][budget]:
                dp[v][budget] = dp[v][prev] + a
    
    # Now, for each vitamin, we want to find the minimum calories needed to achieve at least target intake
    # Since dp[v] is non-decreasing with budget, we can binary search for the minimum budget.
    
    # Precompute the minimum budget for each possible intake for each vitamin
    # For vitamin v, we want min_budget[v][intake] = minimum calories to get at least 'intake'
    # We can do this by finding the first index where dp[v][idx] >= intake
    
    # First, find the maximum possible intake for each vitamin
    max_intakes = [dp[v][X] for v in range(1, 4)]
    
    # Create a mapping from intake to min budget for each vitamin
    # We'll use a list where index is intake, value is min budget
    # Since max intake can be up to N * 2e5 which is too large, we need a different approach.
    # Actually, we can binary search for each query.
    
    # Let's define a function to get min budget for a given target intake for a vitamin
    def get_min_budget(v, target):
        if target <= 0:
            return 0
        if target > max_intakes[v-1]:
            return float('inf')
        # Binary search for the smallest budget such that dp[v][budget] >= target
        lo, hi = 0, X
        ans = float('inf')
        while lo <= hi:
            mid = (lo + hi) // 2
            if dp[v][mid] >= target:
                ans = mid
                hi = mid - 1
            else:
                lo = mid + 1
        return ans
    
    # Binary search for the maximum target
    # Lower bound: 0 (always feasible)
    # Upper bound: min(max_intakes) + 1 (infeasible)
    
    low = 0
    high = min(max_intakes) + 1
    
    while low < high:
        mid = (low + high + 1) // 2
        if mid == 0:
            # 0 is always feasible
            low = mid
            continue
        
        b1 = get_min_budget(1, mid)
        b2 = get_min_budget(2, mid)
        b3 = get_min_budget(3, mid)
        
        if b1 == float('inf') or b2 == float('inf') or b3 == float('inf'):
            high = mid - 1
        else:
            if b1 + b2 + b3 <= X:
                low = mid
            else:
                high = mid - 1
    
    print(low)

if __name__ == "__main__":
    solve()
