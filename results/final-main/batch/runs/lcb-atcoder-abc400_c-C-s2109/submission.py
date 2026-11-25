import sys
import math

def solve():
    n_str = sys.stdin.read().strip()
    if not n_str:
        return
    n = int(n_str)
    
    # Count good integers of form 2*k^2 <= n
    # k^2 <= n // 2
    if n >= 2:
        q1 = n // 2
        k1 = int(math.isqrt(q1))
    else:
        k1 = 0
    
    # Count good integers of form 4*k^2 <= n
    # k^2 <= n // 4
    if n >= 4:
        q2 = n // 4
        k2 = int(math.isqrt(q2))
    else:
        k2 = 0
    
    print(k1 + k2)

if __name__ == "__main__":
    solve()
