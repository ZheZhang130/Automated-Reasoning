import sys
from math import isqrt

def solve():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        N = int(line)
    except ValueError:
        return

    # Good integer X = 2^a * b^2 with a >= 1, b >= 1.
    # Case 1: a is even, a = 2k with k >= 1. Then X = 2^(2k) * b^2 = (2^k * b)^2 = s^2.
    #         Since k >= 1, X must be divisible by 4. Let s = 2^k * b, then s is even.
    #         X = s^2 where s is even. Let s = 2t, then X = 4t^2.
    #         We need 4t^2 <= N => t^2 <= N//4 => t <= isqrt(N // 4).
    # Case 2: a is odd, a = 2k+1 with k >= 0. Then X = 2^(2k+1) * b^2 = 2 * (2^k * b)^2 = 2 * s^2.
    #         We need 2*s^2 <= N => s^2 <= N//2 => s <= isqrt(N // 2).
    # These two cases are disjoint (one is divisible by 4, the other is 2 mod 4).
    # Total count = isqrt(N // 4) + isqrt(N // 2)

    count = isqrt(N // 4) + isqrt(N // 2)
    print(count)

if __name__ == "__main__":
    solve()
