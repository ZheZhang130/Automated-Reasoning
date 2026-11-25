import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    it = iter(input_data)
    N = int(next(it))
    X = int(next(it))
    
    # Group foods by vitamin type
    foods = [defaultdict(list) for _ in range(4)]  # index 1,2,3 used
    for _ in range(N):
        v = int(next(it))
        a = int(next(it))
        c = int(next(it))
        foods[v][c].append(a)
    
    # Sort each vitamin's foods by calorie cost (descending) to try larger A first
    for v in range(1, 4):
        for c in foods[v]:
            foods[v][c].sort(reverse=True)
    
    # Try each possible minimum vitamin value k from 0 to max possible
    # For a fixed k, check if we can achieve at least k for all three vitamins
    # with total calories <= X
    
    # We'll use binary search on the answer k
    # But first, let's find the max possible k for each vitamin individually
    # Actually, we need to check feasibility for a given k
    
    def can_achieve(k):
        if k == 0:
            return True
        # For each vitamin, we need to pick foods to get at least k units
        # with minimum total calories
        # Since we want to minimize calories, for each vitamin we should pick
        # foods with smallest calories first until we reach k units
        
        total_calories = 0
        for v in range(1, 4):
            needed = k
            # Collect all foods for this vitamin and sort by calories
            all_foods = []
            for c in foods[v]:
                for a in foods[v][c]:
                    all_foods.append((c, a))
            all_foods.sort(key=lambda x: x[0])  # sort by calories
            
            current_vitamin = 0
            for c, a in all_foods:
                if current_vitamin < needed:
                    current_vitamin += a
                    total_calories += c
                if current_vitamin >= needed:
                    break
            if current_vitamin < needed:
                return False
        return total_calories <= X
    
    # Binary search for the maximum k
    low = 0
    high = 200000 * 5000  # upper bound
    ans = 0
    
    while low <= high:
        mid = (low + high) // 2
        if can_achieve(mid):
            ans = mid
            low = mid + 1
        else:
            high = mid - 1
    
    print(ans)

if __name__ == "__main__":
    solve()
