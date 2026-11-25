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

    if N == 1:
        print(0)
        return

    count = 0
    s = 1
    while True:
        s2 = s * s
        if s2 > N:
            break
        # For this s, we need 2^k * s^2 <= N, so 2^k <= N / s^2
        # k <= log2(N / s^2)
        # k goes from 1 to floor(log2(N / s^2))
        limit = N // s2
        if limit < 2:
            break
        # k_max = floor(log2(limit))
        # We can compute this by counting how many times we can divide limit by 2
        k_max = 0
        temp = limit
        while temp >= 2:
            temp //= 2
            k_max += 1
        count += k_max
        s += 2  # only odd s

    print(count)

if __name__ == "__main__":
    solve()
