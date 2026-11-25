import sys
from bisect import bisect_left

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    N = int(next(iterator))
    X = int(next(iterator))
    
    # We will build 3 knapsack tables, one for each vitamin (1, 2, 3)
    # Each table is a list of size X+1, where table[v][c] = max vitamin units
    # achievable with exactly c calories (or at most c, since we'll fill carefully)
    # Actually, we want: for each calorie budget c, the max vitamin units.
    # We'll initialize with -1 to indicate unreachable, but since we can always have 0,
    # we can initialize with 0 and update carefully.
    # However, standard 0/1 knapsack: dp[c] = max value with weight <= c.
    # But to combine, we need the minimum calories to achieve at least a certain value.
    # So we'll store: for each calorie budget c, the max vitamin units.
    # Then for a target T, we need the smallest c such that dp[c] >= T.
    
    # Initialize tables with 0 (since 0 units with 0 calories is always possible)
    # But we need to be careful: we want the max units for each calorie budget.
    # We'll use a list of size X+1 for each vitamin.
    
    tables = [[0] * (X + 1) for _ in range(3)]
    
    # Process each food
    for _ in range(N):
        V = int(next(iterator))
        A = int(next(iterator))
        C = int(next(iterator))
        
        # Update the table for vitamin V
        # We do 0/1 knapsack: iterate backwards from X to C
        for c in range(X, C - 1, -1):
            if tables[V-1][c - C] + A > tables[V-1][c]:
                tables[V-1][c] = tables[V-1][c - C] + A
    
    # Now, for each vitamin, we want to find the minimum calories needed to achieve at least T units.
    # Since the table is non-decreasing with c (because if we can achieve T with c calories,
    # we can also achieve T with c+1 calories by not using the extra calorie),
    # we can use binary search.
    # However, our table might not be strictly non-decreasing if we only update when we find a better value.
    # Actually, in standard knapsack, we usually do: dp[c] = max(dp[c], dp[c-C] + A)
    # But we need to ensure that dp[c] is non-decreasing. So after filling, we should do:
    # for c from 1 to X: dp[c] = max(dp[c], dp[c-1])
    # But wait, the problem says "at most X" calories, so we can use any subset with total calories <= X.
    # So the table should represent: for each calorie budget c, the max vitamin units achievable with <= c calories.
    # To achieve that, we can do the knapsack and then do a prefix max.
    
    # Let's redo: first, do the knapsack without prefix max, then do prefix max.
    # But the above code did: for c from X down to C: tables[V-1][c] = max(tables[V-1][c], tables[V-1][c-C] + A)
    # This is correct for "exactly c" if we initialize with -1, but we initialized with 0.
    # Since 0 is the base (0 units with 0 calories), and we can always have 0 units, it's okay.
    # But to get "at most c", we need to do a prefix max after filling.
    
    # Actually, the standard way: 
    # Initialize dp[0] = 0, and dp[c] = -1 for c > 0.
    # Then update: for c from X down to C: if dp[c-C] != -1: dp[c] = max(dp[c], dp[c-C] + A)
    # Then do prefix max: for c from 1 to X: dp[c] = max(dp[c], dp[c-1])
    # But since we initialized with 0, and 0 is always achievable, we can skip the -1.
    # However, the issue is: if we don't do prefix max, then dp[c] might be less than dp[c-1].
    # So we must do prefix max.
    
    # Let's redo the knapsack with prefix max.
    # But the above code already did the knapsack. Now we need to do prefix max for each table.
    
    for v in range(3):
        for c in range(1, X + 1):
            if tables[v][c] < tables[v][c-1]:
                tables[v][c] = tables[v][c-1]
    
    # Now, for each vitamin, we can binary search to find the minimum calories needed for a target T.
    # But note: if the maximum possible for a vitamin is less than T, then T is not achievable.
    
    # We want to find the maximum T such that:
    #   min_calories_1(T) + min_calories_2(T) + min_calories_3(T) <= X
    # where min_calories_v(T) is the smallest c such that tables[v][c] >= T.
    # If for some v, tables[v][X] < T, then T is not achievable for that vitamin.
    
    # First, find the maximum possible T for each vitamin (at budget X)
    max_possible = [tables[v][X] for v in range(3)]
    overall_max = min(max_possible)
    
    # If overall_max is 0, then the answer is 0.
    if overall_max == 0:
        print(0)
        return
    
    # Binary search for the largest T in [0, overall_max] such that the sum of min calories <= X.
    # We know T=0 is always feasible (sum of min calories for 0 is 0, which is <= X).
    # We know T=overall_max+1 is not feasible (because at least one vitamin cannot achieve overall_max+1).
    
    low = 0
    high = overall_max
    ans = 0
    
    while low <= high:
        mid = (low + high) // 2
        total_cal = 0
        feasible = True
        for v in range(3):
            # Binary search for the smallest c such that tables[v][c] >= mid
            # Since tables[v] is non-decreasing, we can use bisect_left
            # But bisect_left works on a sorted list. Our tables[v] is non-decreasing, so it's sorted.
            # However, bisect_left returns the first index where tables[v][c] >= mid.
            # But note: tables[v] might have duplicate values, and bisect_left will return the first one.
            # That's what we want: the smallest c.
            idx = bisect_left(tables[v], mid)
            if idx > X:
                feasible = False
                break
            total_cal += idx
        if feasible and total_cal <= X:
            ans = mid
            low = mid + 1
        else:
            high = mid - 1
    
    print(ans)

if __name__ == "__main__":
    solve()
