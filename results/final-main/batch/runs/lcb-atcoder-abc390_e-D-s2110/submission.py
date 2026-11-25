import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    
    N = int(next(iterator))
    X = int(next(iterator))
    
    foods = []
    for _ in range(N):
        v = int(next(iterator))
        a = int(next(iterator))
        c = int(next(iterator))
        foods.append((v, a, c))
    
    # Group foods by vitamin type
    v1_foods = []
    v2_foods = []
    v3_foods = []
    
    for v, a, c in foods:
        if v == 1:
            v1_foods.append((a, c))
        elif v == 2:
            v2_foods.append((a, c))
        else:
            v3_foods.append((a, c))
    
    # Sort each group by calories (ascending) to try to pick cheapest first
    v1_foods.sort(key=lambda x: x[1])
    v2_foods.sort(key=lambda x: x[1])
    v3_foods.sort(key=lambda x: x[1])
    
    # Precompute prefix sums for calories and vitamin amounts for each group
    def get_prefix_sums(items):
        n = len(items)
        cal_prefix = [0] * (n + 1)
        vit_prefix = [0] * (n + 1)
        for i in range(n):
            cal_prefix[i+1] = cal_prefix[i] + items[i][1]
            vit_prefix[i+1] = vit_prefix[i] + items[i][0]
        return cal_prefix, vit_prefix
    
    cal1, vit1 = get_prefix_sums(v1_foods)
    cal2, vit2 = get_prefix_sums(v2_foods)
    cal3, vit3 = get_prefix_sums(v3_foods)
    
    n1 = len(v1_foods)
    n2 = len(v2_foods)
    n3 = len(v3_foods)
    
    # We want to find the maximum k such that we can get at least k of each vitamin
    # with total calories <= X
    
    # Binary search on k
    low = 0
    high = 200000  # Max possible vitamin amount
    ans = 0
    
    while low <= high:
        mid = (low + high) // 2
        if mid == 0:
            # Always possible (empty set)
            ans = max(ans, mid)
            low = mid + 1
            continue
        
        # Check if it's possible to get at least mid of each vitamin with <= X calories
        # For each vitamin, we need to select a subset of foods to get >= mid
        # To minimize calories, we should pick the cheapest foods that give us enough vitamin
        
        # For each vitamin type, find the minimum calories needed to get >= mid
        # Since foods are sorted by calories, we can use prefix sums
        
        # For vitamin 1: find smallest i such that vit1[i] >= mid
        # We need to find the minimum calories to get at least mid
        # Since we can pick any subset, we should pick the cheapest ones that give us enough
        
        # Actually, since foods are sorted by calories, the prefix sum gives the cheapest way
        # to get a certain amount. But we might need to skip some expensive ones if they give little vitamin.
        # However, since we sorted by calories, the prefix sum is the minimum calories to get
        # the first i items. But we might not need all items.
        
        # Better approach: for each vitamin, we want to find the minimum calories to get >= mid.
        # Since foods are sorted by calories, we can iterate and find the point where we get enough.
        
        # But wait, we can pick any subset. The optimal strategy for a single vitamin is to pick
        # the cheapest foods until we reach the target. So for each vitamin, we find the minimum
        # calories to get >= mid by taking the cheapest foods.
        
        # For vitamin 1:
        needed1 = mid
        if needed1 <= 0:
            cost1 = 0
        else:
            # Find the smallest i such that vit1[i] >= needed1
            # Since vit1 is increasing, we can use binary search or just iterate
            # But since we have prefix sums, we can find the first i where vit1[i] >= needed1
            # However, we need to be careful: we might not need to take all items up to i.
            # Actually, since we sorted by calories, taking the first i items gives the minimum
            # calories to get vit1[i] amount. But we might get more than needed1.
            # So we need to find the smallest i such that vit1[i] >= needed1.
            
            # Since vit1 is non-decreasing, we can use bisect or just iterate.
            # But we don't have a direct way to get the exact amount. We need to find the
            # minimum calories to get at least needed1.
            
            # Since we sorted by calories, the prefix sum is the minimum calories to get
            # the first i items. But we might not need all items. Actually, we do need to take
            # items in order of increasing calories to minimize total calories.
            
            # So we need to find the smallest i such that vit1[i] >= needed1.
            # We can do this by iterating or using bisect.
            
            # Let's iterate since n is small (up to 5000)
            cost1 = 0
            current_vit = 0
            for i in range(n1):
                current_vit += v1_foods[i][0]
                cost1 += v1_foods[i][1]
                if current_vit >= needed1:
                    break
            else:
                # Not enough even with all items
                cost1 = float('inf')
        
        # Similarly for vitamin 2
        needed2 = mid
        if needed2 <= 0:
            cost2 = 0
        else:
            cost2 = 0
            current_vit = 0
            for i in range(n2):
                current_vit += v2_foods[i][0]
                cost2 += v2_foods[i][1]
                if current_vit >= needed2:
                    break
            else:
                cost2 = float('inf')
        
        # Similarly for vitamin 3
        needed3 = mid
        if needed3 <= 0:
            cost3 = 0
        else:
            cost3 = 0
            current_vit = 0
            for i in range(n3):
                current_vit += v3_foods[i][0]
                cost3 += v3_foods[i][1]
                if current_vit >= needed3:
                    break
            else:
                cost3 = float('inf')
        
        total_cost = cost1 + cost2 + cost3
        if total_cost <= X:
            ans = max(ans, mid)
            low = mid + 1
        else:
            high = mid - 1
    
    print(ans)

if __name__ == "__main__":
    solve()
