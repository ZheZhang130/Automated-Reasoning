import sys

def solve():
    input_data = sys.stdin.read().split()
    it = iter(input_data)
    N = int(next(it))
    X = int(next(it))
    
    # Group foods by vitamin type
    foods_by_vitamin = [list() for _ in range(4)]  # 1,2,3,4 (4 unused)
    
    for _ in range(N):
        v = int(next(it))
        a = int(next(it))
        c = int(next(it))
        foods_by_vitamin[v].append((a, c))
    
    # For each vitamin, compute max intake for each calorie budget using 0/1 knapsack
    max_intake = [0] * (X + 1)
    
    for v in range(1, 4):
        items = foods_by_vitamin[v]
        dp = [-1] * (X + 1)
        dp[0] = 0
        
        for a, c in items:
            # 0/1 knapsack: iterate backwards
            for budget in range(X, c - 1, -1):
                if dp[budget - c] != -1:
                    new_val = dp[budget - c] + a
                    if new_val > dp[budget]:
                        dp[budget] = new_val
        
        # Convert to prefix max: dp[c] = max intake with at most c calories
        for c in range(1, X + 1):
            dp[c] = max(dp[c], dp[c - 1])
        
        max_intake[v] = dp
    
    # Binary search for the maximum possible minimum
    total_v1 = sum(a for a, c in foods_by_vitamin[1])
    total_v2 = sum(a for a, c in foods_by_vitamin[2])
    total_v3 = sum(a for a, c in foods_by_vitamin[3])
    upper_bound = min(total_v1, total_v2, total_v3)
    
    left = 0
    right = upper_bound
    ans = 0
    
    while left <= right:
        mid = (left + right) // 2
        if mid == 0:
            ans = max(ans, 0)
            left = mid + 1
            continue
        
        # Check if we can get at least mid for each vitamin
        needed_calories = []
        possible = True
        
        for v in range(1, 4):
            # Find minimum calories to get at least mid
            c_needed = None
            for c in range(X + 1):
                if max_intake[v][c] >= mid:
                    c_needed = c
                    break
            
            if c_needed is None:
                possible = False
                break
            
            needed_calories.append(c_needed)
        
        if possible:
            total_needed = sum(needed_calories)
            if total_needed <= X:
                ans = mid
                left = mid + 1
            else:
                right = mid - 1
        else:
            right = mid - 1
    
    print(ans)

if __name__ == "__main__":
    solve()
