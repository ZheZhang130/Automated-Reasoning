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
    # (i±0.5, j±0.5) is entirely inside the circle of radius R centered at origin.
    # The farthest corner from origin for a square centered at (i, j) is at distance:
    # sqrt((|i|+0.5)^2 + (|j|+0.5)^2) <= R
    # So we need (|i|+0.5)^2 + (|j|+0.5)^2 <= R^2
    # Let x = |i|, y = |j|. Then (x+0.5)^2 + (y+0.5)^2 <= R^2
    # We can iterate over x from 0 to R-0.5 (i.e., x <= R-1 since x is integer)
    # For each x, find max y such that (y+0.5)^2 <= R^2 - (x+0.5)^2
    # Then y_max = floor(sqrt(R^2 - (x+0.5)^2) - 0.5)
    # But we must ensure y >= 0.

    R2 = R * R
    count = 0

    # x goes from 0 to R (since x+0.5 <= R => x <= R-0.5, so max integer x is R-1 if R>=1)
    # Actually, if x = R, then (R+0.5)^2 > R^2, so x must be < R.
    # So x ranges from 0 to R-1 inclusive.
    for x in range(R):
        # Compute max y such that (y+0.5)^2 <= R^2 - (x+0.5)^2
        val = R2 - (x + 0.5)**2
        if val <= 0:
            continue
        max_y_plus_05 = math.sqrt(val)
        max_y = max_y_plus_05 - 0.5
        if max_y < 0:
            continue
        y_max = int(max_y)  # floor
        if y_max < 0:
            y_max = -1
        
        # For this x, y can range from 0 to y_max inclusive
        if y_max >= 0:
            count += (y_max + 1)
    
    # Now account for symmetry:
    # x=0: only 1 column (i=0), but y from 0 to y_max gives (y_max+1) squares, each with 2 choices for j (except j=0 which is 1)
    # Actually, let's think differently:
    # For x > 0, each x corresponds to two columns: i = x and i = -x
    # For x = 0, only one column: i = 0
    # Similarly for y.
    
    # So we need to count:
    # For x=0: y from 0 to y_max(0) -> for each y, j can be 0 only? No.
    # Let's restructure:
    # We iterate x from 0 to R-1.
    # For each x, we find y_max such that for all y in [0, y_max], the square is valid.
    # Then:
    #   If x == 0:
    #       For each y in [0, y_max], we have j = 0 only? No, j can be positive or negative.
    #       Actually, the condition is symmetric in j. So for a given y, j can be y or -y, but if y=0, only one.
    #       So for x=0, number of j values for a given y is: 1 if y=0, else 2.
    #       But we are iterating y from 0 to y_max. So total for x=0 is: 1 (for y=0) + 2*(y_max) if y_max>0.
    #       Actually, simpler: for x=0, the number of j values is: 1 + 2*y_max (if y_max>=0)
    #   If x > 0:
    #       For each y in [0, y_max], we have i = x and i = -x (2 choices), and for each, j can be y or -y (2 choices if y>0, 1 if y=0).
    #       So for a fixed x>0 and fixed y>0: 2 * 2 = 4 squares.
    #       For y=0: 2 * 1 = 2 squares.
    #       So total for x>0: 2 * (1 + 2*y_max) if we consider y from 0 to y_max? 
    #       Actually, for each y in [0, y_max]:
    #           if y==0: 2 squares (i=x,-x, j=0)
    #           if y>0: 4 squares (i=x,-x, j=y,-y)
    #       So total = 2 + 4*y_max
    #       But note: we are iterating y from 0 to y_max, so we have y_max+1 values of y.
    #       So total = 2 (for y=0) + 4*y_max (for y=1..y_max) = 2 + 4*y_max.
    
    # However, the above logic is flawed because we are double counting? Let me re-express.
    
    # Better approach:
    # Count for x=0 separately, then for x>0.
    # For x=0:
    #   y_max0 = floor(sqrt(R^2 - 0.25) - 0.5)
    #   Then for y from 0 to y_max0:
    #       if y==0: 1 square (i=0, j=0)
    #       else: 2 squares (i=0, j=y and i=0, j=-y)
    #   So total for x=0: 1 + 2*y_max0
    # For x>0:
    #   For each x from 1 to R-1:
    #       y_max = floor(sqrt(R^2 - (x+0.5)^2) - 0.5)
    #       if y_max < 0: continue
    #       For y=0: 2 squares (i=x,-x, j=0)
    #       For y from 1 to y_max: 4 squares each (i=x,-x, j=y,-y)
    #       So total for this x: 2 + 4*y_max
    #   Sum over x from 1 to R-1.
    
    # But wait, the above for x=0: 
    #   y_max0 = floor(sqrt(R^2 - 0.25) - 0.5)
    #   Then count = 1 + 2*y_max0
    # For x>0, for each x, count = 2 + 4*y_max
    # Total = (1 + 2*y_max0) + sum_{x=1}^{R-1} (2 + 4*y_max(x))
    
    # However, note that for x=0, we have only one column, and for x>0, two columns.
    # And for each column, the number of rows is determined by y_max.
    
    # Let me test with R=2:
    #   x=0: y_max0 = floor(sqrt(4-0.25)-0.5) = floor(sqrt(3.75)-0.5) = floor(1.936-0.5)=floor(1.436)=1
    #        count for x=0: 1 + 2*1 = 3
    #   x=1: y_max = floor(sqrt(4-(1.5)^2)-0.5) = floor(sqrt(4-2.25)-0.5)=floor(sqrt(1.75)-0.5)=floor(1.322-0.5)=floor(0.822)=0
    #        count for x=1: 2 + 4*0 = 2
    #   Total = 3+2 = 5 -> matches sample.
    
    # R=4:
    #   x=0: y_max0 = floor(sqrt(16-0.25)-0.5)=floor(sqrt(15.75)-0.5)=floor(3.968-0.5)=floor(3.468)=3
    #        count: 1+2*3=7
    #   x=1: y_max=floor(sqrt(16-2.25)-0.5)=floor(sqrt(13.75)-0.5)=floor(3.708-0.5)=floor(3.208)=3 -> 2+4*3=14
    #   x=2: y_max=floor(sqrt(16-6.25)-0.5)=floor(sqrt(9.75)-0.5)=floor(3.122-0.5)=floor(2.622)=2 -> 2+4*2=10
    #   x=3: y_max=floor(sqrt(16-12.25)-0.5)=floor(sqrt(3.75)-0.5)=floor(1.936-0.5)=floor(1.436)=1 -> 2+4*1=6
    #   Total = 7+14+10+6 = 37 -> matches.
    
    # So the formula is:
    #   count = (1 + 2*y_max0) + sum_{x=1}^{R-1} (2 + 4*y_max(x))
    # where y_max(x) = floor(sqrt(R^2 - (x+0.5)^2) - 0.5)
    
    # But note: for x=0, we have y_max0, and for x>0, we have y_max(x).
    # We can write a loop for x from 0 to R-1, and handle x=0 separately.
    
    # However, we can also write a unified loop if we adjust the multiplier for x=0.
    # For x=0: multiplier for the count per y is 1 for y=0 and 2 for y>0 -> total 1+2*y_max0
    # For x>0: multiplier is 2 for y=0 and 4 for y>0 -> total 2+4*y_max
    # So we can do:
    #   total = 0
    #   for x in range(R):
    #       val = R2 - (x+0.5)**2
    #       if val <= 0:
    #           break
    #       max_y_plus_05 = math.sqrt(val)
    #       y_max = int(max_y_plus_05 - 0.5)
    #       if y_max < 0:
    #           y_max = -1
    #       if x == 0:
    #           total += 1 + 2 * y_max
    #       else:
    #           total += 2 + 4 * y_max
    #   print(total)
    
    # But wait, for x=0, we have only one column, so the count is 1 + 2*y_max (which is 1 for y=0 and 2 for each y>0).
    # For x>0, we have two columns, so for y=0: 2 squares, for y>0: 4 squares -> 2 + 4*y_max.
    # This matches.
    
    # However, note that for x=0, y_max might be negative? But since R>=1, (x+0.5)^2 <= (0.5)^2=0.25 <= R^2, so val>=0.
    # And max_y_plus_05 >= sqrt(R^2-0.25) >= sqrt(1-0.25)=sqrt(0.75)~0.866, so max_y = max_y_plus_05-0.5 >= 0.366, so y_max>=0.
    # So y_max is nonnegative for x=0.
    
    # Let's code accordingly.
    
    total = 0
    for x in range(R):
        val = R2 - (x + 0.5)**2
        if val <= 0:
            break
        max_y_plus_05 = math.sqrt(val)
        y_max = int(max_y_plus_05 - 0.5)
        if y_max < 0:
            y_max = -1
        
        if x == 0:
            total += 1 + 2 * y_max
        else:
            total += 2 + 4 * y_max
    
    print(total)

if __name__ == '__main__':
    solve()
