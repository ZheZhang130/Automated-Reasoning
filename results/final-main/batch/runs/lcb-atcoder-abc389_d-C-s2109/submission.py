import sys
import math

def solve():
    input_data = sys.stdin.read().strip()
    if not input_data:
        return
    R = int(input_data)
    
    # We need to count integer pairs (i, j) such that the square centered at (i, j)
    # is completely inside the circle of radius R centered at (0, 0).
    # The square has corners at (i +/- 0.5, j +/- 0.5).
    # The farthest corner from origin is at distance sqrt((|i|+0.5)^2 + (|j|+0.5)^2).
    # Condition: (|i| + 0.5)^2 + (|j| + 0.5)^2 <= R^2
    # Multiply by 4: (2|i| + 1)^2 + (2|j| + 1)^2 <= 4*R^2
    
    limit_sq = 4 * R * R
    
    ans = 0
    y = R - 1  # Candidate for |j|, starting from max possible
    
    # We iterate x = |i| from 0 to R-1
    for x in range(R):
        # For current x, we need to find max y such that (2x+1)^2 + (2y+1)^2 <= limit_sq
        # We decrease y until condition is met or y becomes negative
        
        # Check if even y=0 works
        if (2*x + 1)**2 + 1 > limit_sq:
            # Even the smallest square in this column doesn't fit
            break
            
        # Decrease y until condition is met
        while y >= 0 and (2*x + 1)**2 + (2*y + 1)**2 > limit_sq:
            y -= 1
        
        if y < 0:
            break
            
        # Now y is the max |j| that works for this x
        # Number of j values: 2*y + 1 (from -y to y)
        count = 2 * y + 1
        
        if x == 0:
            ans += count
        else:
            ans += 2 * count
            
    print(ans)

if __name__ == "__main__":
    solve()
