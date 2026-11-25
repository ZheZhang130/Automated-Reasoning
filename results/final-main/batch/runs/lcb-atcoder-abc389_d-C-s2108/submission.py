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

    # We need to count integer pairs (i, j) such that the square centered at (i, j)
    # is completely inside the circle of radius R centered at (0, 0).
    # The farthest corner of the square centered at (i, j) is at distance:
    # sqrt((|i| + 0.5)^2 + (|j| + 0.5)^2) <= R
    # Multiply by 2 to avoid floats:
    # (2*|i| + 1)^2 + (2*|j| + 1)^2 <= 4*R^2

    # Let x = |i|, y = |j|
    # (2x + 1)^2 + (2y + 1)^2 <= 4R^2
    # Let A = 2x + 1, B = 2y + 1
    # A^2 + B^2 <= 4R^2
    # A, B are odd positive integers (since x, y >= 0)
    # x = (A - 1) / 2, y = (B - 1) / 2

    # We iterate over possible values of x (from 0 to R-1)
    # For each x, we find the maximum y such that the condition holds.
    # Since the condition is monotonic in y, we can use a decreasing pointer.

    limit_sq = 4 * R * R
    ans = 0
    y_max = R  # Start with a safe upper bound for y (actually R-1 is enough, but R is safe)
    
    # We'll iterate x from 0 upwards. For each x, we find the max y.
    # Since (2x+1)^2 + (2y+1)^2 <= 4R^2, as x increases, y_max decreases.
    
    x = 0
    while True:
        A = 2 * x + 1
        A_sq = A * A
        
        if A_sq >= limit_sq:
            # Even with y=0, (2x+1)^2 > 4R^2, so no more squares fit.
            break
        
        # We need (2y+1)^2 <= limit_sq - A_sq
        # Let rem = limit_sq - A_sq
        # We need the largest odd B such that B^2 <= rem
        # B = floor(sqrt(rem))
        # But B must be odd. So we take floor(sqrt(rem)) and adjust to nearest odd <= that.
        
        rem = limit_sq - A_sq
        if rem <= 0:
            break
            
        B_max = int(math.isqrt(rem))
        
        # B must be odd and <= B_max
        if B_max % 2 == 0:
            B_max -= 1
        
        if B_max < 1:
            # No odd B >= 1 satisfies the condition
            break
        
        y = (B_max - 1) // 2
        
        # Now, for this x, y can range from 0 to y (inclusive)
        # Number of choices for j: 2*y + 1 (since j can be -y, ..., y)
        count_y = 2 * y + 1
        
        if x == 0:
            ans += count_y
        else:
            ans += 2 * count_y
        
        x += 1
    
    print(ans)

if __name__ == "__main__":
    solve()
