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

    # Count numbers of form 2*k^2 <= N
    # k^2 <= N/2  => k <= sqrt(N/2)
    # Count numbers of form 4*k^2 <= N
    # k^2 <= N/4  => k <= sqrt(N/4)
    
    # Use integer square root to avoid floating point issues
    def isqrt(n):
        if n < 0:
            return -1
        if n == 0:
            return 0
        x = int(math.isqrt(n))
        return x

    count1 = 0
    count2 = 0
    
    if N >= 2:
        q1 = N // 2
        count1 = isqrt(q1)
    
    if N >= 4:
        q2 = N // 4
        count2 = isqrt(q2)
    
    print(count1 + count2)

if __name__ == "__main__":
    solve()
