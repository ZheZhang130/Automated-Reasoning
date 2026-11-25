import sys
import math

def solve():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        N = int(line)
    except ValueError:
        return

    # Count good integers of form 2*k^2 <= N
    # k^2 <= N/2  => k <= sqrt(N/2)
    # Count good integers of form 4*k^2 <= N
    # k^2 <= N/4  => k <= sqrt(N/4)
    
    # Use integer square root to avoid floating point issues
    # For a non-negative integer q, find largest k such that k*k <= q
    
    def isqrt(n):
        if n < 0:
            return 0
        if n == 0:
            return 0
        # Use math.isqrt for Python 3.8+
        return math.isqrt(n)
    
    count1 = 0
    if N >= 2:
        q1 = N // 2
        count1 = isqrt(q1)
    
    count2 = 0
    if N >= 4:
        q2 = N // 4
        count2 = isqrt(q2)
    
    print(count1 + count2)

if __name__ == "__main__":
    solve()
