import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    it = iter(input_data)
    N = int(next(it))
    X = int(next(it))
    
    # Group foods by vitamin type
    foods = [defaultdict(int) for _ in range(4)]  # 1,2,3,4 (4 unused)
    
    for _ in range(N):
        v = int(next(it))
        a = int(next(it))
        c = int(next(it))
        foods[v][c] += a
    
    # Binary search for the maximum possible minimum
    def can_achieve(min_val):
        # Check if we can get at least min_val for each vitamin with total calories <= X
        used_calories = 0
        
        for v in range(1, 4):
            if min_val == 0:
                continue
            # We need at least min_val of vitamin v
            # Each food gives exactly 1 unit of its vitamin
            # So we want to pick the cheapest foods (by calories) to reach min_val
            
            # Get all foods for this vitamin
            items = []
            for c, a in foods[v].items():
                # a items with c calories each
                for _ in range(a):
                    items.append(c)
            
            items.sort()
            
            for cal in items:
                used_calories += cal
                if used_calories > X:
                    return False
                min_val -= 1
        
        return used_calories <= X
    
    # Binary search
    left = 0
    right = 200000 * 3 + 1  # Max possible sum
    ans = 0
    
    while left <= right:
        mid = (left + right) // 2
        if can_achieve(mid):
            ans = mid
            left = mid + 1
        else:
            right = mid - 1
    
    print(ans)

if __name__ == "__main__":
    solve()
