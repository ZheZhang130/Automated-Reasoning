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
    # The square has corners at (i +/- 0.5, j +/- 0.5).
    # The farthest corner from origin is at distance sqrt((|i|+0.5)^2 + (|j|+0.5)^2).
    # Condition: (|i|+0.5)^2 + (|j|+0.5)^2 <= R^2
    # Multiply by 4: (2|i|+1)^2 + (2|j|+1)^2 <= 4R^2
    # Let x = |i|, y = |j|. Then (2x+1)^2 + (2y+1)^2 <= 4R^2.
    # We iterate x from 0 to R-1 (since 2x+1 > 2R when x >= R, impossible).
    # For each x, find max y such that (2x+1)^2 + (2y+1)^2 <= 4R^2.
    # Then for this x, y can be 0, 1, ..., max_y.
    # Number of j values for a given y is 2*y + 1 (positive, negative, zero).
    # For x=0, i can be 0 only (1 choice). For x>0, i can be x or -x (2 choices).
    
    ans = 0
    limit_sq = 4 * R * R
    
    # Start with y candidate at R-1 (since 2y+1 <= 2R => y <= R-0.5 => y <= R-1 for integer)
    y = R - 1
    
    for x in range(R):
        # For current x, we need (2x+1)^2 + (2y+1)^2 <= limit_sq
        # We decrease y until condition holds or y < 0
        while y >= 0:
            lhs = (2*x + 1)**2 + (2*y + 1)**2
            if lhs <= limit_sq:
                break
            y -= 1
        
        if y < 0:
            # No valid y for this x and any larger x
            break
        
        # Add contribution
        if x == 0:
            ans += 2 * y + 1
        else:
            ans += 2 * (2 * y + 1)
    
    print(ans)

if __name__ == "__main__":
    solve()
