import sys
import math

def solve():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        R = int(line)
    except ValueError:
        return

    # We need to count integer pairs (i, j) such that the square with corners
    # (i+/-0.5, j+/-0.5) is inside the circle of radius R centered at (0,0).
    # The condition is that the farthest corner from the origin is within distance R.
    # The farthest corner of the square centered at (i, j) is at distance:
    # sqrt((i + 0.5)^2 + (j + 0.5)^2) <= R
    # So we need (i + 0.5)^2 + (j + 0.5)^2 <= R^2
    # Let x = i + 0.5, y = j + 0.5. Then x and y are half-integers: k + 0.5 for integer k.
    # We can rewrite: (2x)^2 + (2y)^2 <= (2R)^2
    # Let X = 2x = 2i + 1, Y = 2y = 2j + 1. Then X and Y are odd integers.
    # Condition: X^2 + Y^2 <= (2R)^2
    # We need to count the number of pairs (X, Y) of odd integers satisfying this.
    # Since the circle is symmetric, we can count for X >= 0 and multiply appropriately.
    # For X = 0, Y must be odd, but 0 is even, so X=0 is not possible.
    # Actually, X and Y are odd integers, so they can be positive or negative.
    # We can count for X > 0 and Y > 0, then multiply by 4, and handle X=0 or Y=0 if possible.
    # But X and Y are odd, so they can never be 0.
    # So we count pairs (X, Y) with X > 0, Y > 0, X odd, Y odd, X^2 + Y^2 <= (2R)^2.
    # Then multiply by 4.

    limit = 2 * R
    limit_sq = limit * limit

    count = 0
    # We iterate X from 1 to limit, step 2 (only odd numbers)
    # For each X, we find the maximum odd Y such that Y^2 <= limit_sq - X^2
    # Y_max = floor(sqrt(limit_sq - X^2))
    # Then we take the largest odd number <= Y_max.
    # If Y_max < 1, then no Y exists for this X.
    
    # Optimization: iterate X from 1 to limit, step 2
    # For each X, compute max_Y_sq = limit_sq - X^2
    # If max_Y_sq < 1, break (since X is increasing, max_Y_sq will decrease)
    # max_Y = floor(sqrt(max_Y_sq))
    # Then we need the largest odd number <= max_Y.
    # If max_Y is even, then max_odd = max_Y - 1
    # If max_Y is odd, then max_odd = max_Y
    # But we also need max_odd >= 1. If max_odd < 1, then count += 0.
    
    # However, we need to be careful: we are counting pairs (X, Y) with X > 0, Y > 0.
    # Since the circle is symmetric, the number of pairs with X > 0, Y > 0 is the same as
    # X < 0, Y > 0, etc. So we multiply by 4.
    
    # Let's iterate X from 1 to limit, step 2.
    # For each X, compute max_Y = floor(sqrt(limit_sq - X^2))
    # Then max_odd = max_Y if max_Y is odd else max_Y - 1
    # If max_odd >= 1, then we add max_odd to count.
    
    # But note: we must ensure that max_odd is positive. If max_odd < 1, then we add 0.
    
    # Let's code this.
    
    X = 1
    while X <= limit:
        max_Y_sq = limit_sq - X * X
        if max_Y_sq < 1:
            break
        max_Y = int(math.isqrt(max_Y_sq))
        # Now we want the largest odd number <= max_Y
        if max_Y % 2 == 0:
            max_odd = max_Y - 1
        else:
            max_odd = max_Y
        
        if max_odd >= 1:
            count += max_odd
        
        X += 2
    
    # Multiply by 4 for the four quadrants
    ans = count * 4
    print(ans)

if __name__ == "__main__":
    solve()
