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

    limit = 2 * R
    limit_sq = limit * limit

    count = 0
    # We iterate X from 1 to limit, step 2 (only odd numbers)
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
            # For each odd Y from 1 to max_odd, compute contribution
            for Y in range(1, max_odd + 1, 2):
                if X == 1 and Y == 1:
                    count += 1
                elif X == 1 or Y == 1:
                    count += 2
                else:
                    count += 4
        
        X += 2
    
    print(count)

if __name__ == "__main__":
    solve()
