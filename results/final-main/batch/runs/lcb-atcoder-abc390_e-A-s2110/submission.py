import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    N = int(next(iterator))
    X = int(next(iterator))
    
    # Group foods by vitamin type
    # foods[v] = list of (A, C) for vitamin v (v is 1, 2, or 3)
    foods = defaultdict(list)
    
    for _ in range(N):
        v = int(next(iterator))
        a = int(next(iterator))
        c = int(next(iterator))
        foods[v].append((a, c))
    
    # Sort each group by calories ascending (to try to pick more items with less cost)
    for v in foods:
        foods[v].sort(key=lambda x: x[1])
    
    # We want to find the maximum min_vitamin
    # Binary search on the answer: can we achieve at least K units for each vitamin?
    # For a fixed K, we need to select items such that:
    #   sum(A_i) >= K for each vitamin v
    #   sum(C_i) <= X
    # To maximize the chance of fitting within X, for each vitamin, we should pick
    # the items with the smallest calories that sum up to at least K.
    # However, we can pick more than K for a vitamin if it helps (but we don't need to).
    # Actually, for a fixed K, the optimal strategy for each vitamin is to pick the
    # cheapest items until we reach at least K. Then sum the calories.
    # If the total calories <= X, then K is achievable.
    
    # Precompute prefix sums of calories for each vitamin group to quickly find
    # the minimum calories needed to get at least K units.
    
    # For each vitamin, we want to find the minimum calories to get at least K units.
    # Since items are sorted by calories, we just take the first m items such that
    # sum(A) >= K.
    
    # Let's precompute for each vitamin the minimum calories needed for each possible K.
    # K can range from 0 to sum(A) for that vitamin.
    
    # Actually, we can just compute on the fly or precompute up to max possible K.
    # Max K is sum of all A_i for a vitamin, which can be up to 5000 * 200000 = 1e9,
    # but we only care up to X (since if K > X, we can't possibly get it because A_i >= 1).
    # Actually, the constraint is on calories, not on A. But if K is very large, 
    # we might not be able to achieve it. The maximum possible K we need to check is 
    # bounded by the total A available, but also practically by X (since each A_i >= 1, 
    # and we need at least K items if each gives 1, but A_i can be large).
    # However, the binary search will handle the range. Let's set high bound to sum of all A_i for a vitamin.
    # But that can be large. Instead, note that if K > X, it's impossible because each item has C_i >= 1,
    # and we need at least K items if each gives 1 unit, but actually one item can give many units.
    # However, the minimum calories to get K units is at least K (if each item gives at least 1 unit and costs at least 1).
    # So if K > X, it's impossible. So we can binary search in [0, X].
    
    # Precompute min_calories[v][k] = minimum calories to get at least k units of vitamin v.
    # We only need to compute up to k = X, because if k > X, it's impossible.
    
    max_k = X  # We only care up to X
    
    min_cal = {}
    
    for v, items in foods.items():
        # items is sorted by calories ascending
        # Compute prefix sums of A and C
        prefix_a = [0]
        prefix_c = [0]
        for a, c in items:
            prefix_a.append(prefix_a[-1] + a)
            prefix_c.append(prefix_c[-1] + c)
        
        # For each k from 1 to len(prefix_a)-1, find the smallest index i such that prefix_a[i] >= k
        # Then min_cal[v][k] = prefix_c[i]
        # We can do this by binary search or two pointers. Since prefix_a is sorted, we can use bisect.
        # But since we are iterating k, we can just iterate through the items.
        
        # Actually, we can just store the result for each k that is achievable.
        # But we want min_cal[v][k] for k in [1, max_k].
        # If k is not achievable (i.e., total A < k), then it's infinity.
        
        # Let's compute for all k from 1 to len(prefix_a)-1
        # We can use a pointer to find the smallest i for each k.
        # But since k increases, the required i also increases (non-decreasing).
        
        # We can precompute for all k up to max_k.
        # Initialize with infinity
        current_k = 0
        current_c = 0
        idx = 0
        n_items = len(items)
        
        # We'll create a list for this vitamin, indexed by k
        # But k can be up to max_k. Let's use a list of size max_k + 1, initialized to infinity.
        # However, max_k can be 5000, which is fine.
        
        # Actually, we can just compute the min calories for each k that is achievable.
        # Then for k > total A, it's infinity.
        
        # Let's use a list for this vitamin
        v_min_cal = [float('inf')] * (max_k + 1)
        
        # We can iterate through the items and update the range of k that this item covers.
        # But it's easier to just iterate k from 1 to total A and find the smallest i.
        # Since prefix_a is sorted, we can use bisect_left.
        
        import bisect
        
        for k in range(1, max_k + 1):
            # Find the smallest i such that prefix_a[i] >= k
            # prefix_a[0] = 0, so we start from i=1
            # We want the smallest i such that prefix_a[i] >= k
            # Since prefix_a is sorted, we can use bisect_left
            # But bisect_left works on a list, and prefix_a is a list.
            # However, prefix_a can be large, but we only need up to max_k.
            # Actually, we can just iterate i from 1 to n_items and update the k range.
            pass
        
        # Alternative: iterate i from 1 to n_items, and for each i, the k range covered is (prefix_a[i-1], prefix_a[i]]
        # For k in that range, the min calories is prefix_c[i].
        # But we want the minimum calories for each k, which is prefix_c[i] for the smallest i such that prefix_a[i] >= k.
        # So for k in (prefix_a[i-1], prefix_a[i]], the answer is prefix_c[i].
        
        # Let's do that.
        prev_a = 0
        for i in range(1, n_items + 1):
            curr_a = prefix_a[i]
            curr_c = prefix_c[i]
            # For k in (prev_a, curr_a], the min calories is curr_c
            start_k = prev_a + 1
            end_k = curr_a
            if start_k <= max_k:
                # Fill v_min_cal[start_k : end_k + 1] with curr_c
                # But we only need to fill up to max_k
                fill_end = min(end_k, max_k)
                for k in range(start_k, fill_end + 1):
                    v_min_cal[k] = curr_c
            prev_a = curr_a
        
        # For k > prev_a (which is total A), it's infinity (already initialized)
        min_cal[v] = v_min_cal
    
    # Now binary search for the maximum K
    low = 0
    high = X  # Because if K > X, it's impossible (since each item has C_i >= 1, and we need at least K items if each gives 1, but actually one item can give many units. However, the minimum calories to get K units is at least K if each item gives at least 1 unit and costs at least 1. But actually, an item can give many units and cost 1. So the minimum calories can be less than K. However, we have the constraint that total calories <= X. So if K > X, it's still possible? Let's think: if we have an item with A=1000, C=1, then we can get 1000 units with 1 calorie. So K can be larger than X. But the problem says C_i <= X, and we have N items. The maximum possible K is sum of all A_i for a vitamin, which can be large. But we only need to check up to the maximum possible K that is achievable. However, the binary search range should be [0, sum of all A_i for a vitamin]. But that can be large. However, we can set high to X + max(A_i) or something. But actually, the maximum possible K is bounded by the total A available, but we can set high to X + 200000 (max A_i) or even 1e9. But binary search on 1e9 is fine (log2(1e9) ~ 30).
    # However, we can set high to X + max_possible_A, but max_possible_A is 200000, so high = X + 200000 is fine.
    # But actually, the maximum possible K is sum of all A_i for a vitamin, which can be 5000 * 200000 = 1e9.
    # So we set high = 1e9 + 7 or something. But let's use a safe upper bound: X + 200000 is not enough.
    # Let's use high = 10**9 + 7.
    high = 10**9 + 7
    
    ans = 0
    
    while low <= high:
        mid = (low + high) // 2
        if mid == 0:
            # Always possible (0 calories, 0 vitamins)
            ans = max(ans, mid)
            low = mid + 1
            continue
        
        # Check if mid is achievable
        total_cal = 0
        possible = True
        
        for v in [1, 2, 3]:
            if v not in min_cal:
                # No items for this vitamin, so we can't get any units
                if mid > 0:
                    possible = False
                    break
            else:
                v_min_cal = min_cal[v]
                if mid > len(v_min_cal) - 1:
                    # mid is larger than the maximum achievable K for this vitamin
                    possible = False
                    break
                if v_min_cal[mid] == float('inf'):
                    possible = False
                    break
                total_cal += v_min_cal[mid]
        
        if possible and total_cal <= X:
            ans = mid
            low = mid + 1
        else:
            high = mid - 1
    
    print(ans)

if __name__ == '__main__':
    solve()
