import sys
from functools import lru_cache
from math import comb

def solve(n, mod):
    half = n // 2
    max_edges = n * (n - 1) // 2
    width = 9
    bits = 8 * width
    choose = [[comb(r, b) for b in range(r + 1)] for r in range(n + 1)]

    @lru_cache(None)
    def factor(a, b, r):
        labels = choose[r][b]
        step = bits * a
        value = 0
        for j in range(b, -1, -1):
            c = labels * choose[b][j]
            if (b - j) & 1:
                c = -c
            value = (value << step) | (c % mod)
        return value << (bits * (b * (b - 1) // 2))

    def coefficients(value):
        length = (value.bit_length() + bits - 1) // bits
        raw = value.to_bytes(length * width, 'little')
        return (int.from_bytes(raw[i:i + width], 'little') % mod
                for i in range(0, len(raw), width))

    def reduce_packed(value):
        return int.from_bytes(
            b''.join(c.to_bytes(width, 'little') for c in coefficients(value)),
            'little'
        )

    # Entries describe the totals in even and odd layers, and the
    # size and parity of the last layer. A coefficient slot is in base
    # 2**72, wide enough to sum all incoming convolutions without carry.
    dp = [{} for _ in range(n + 1)]
    dp[1][(1, 0, 1, 0)] = 1
    for used in range(1, n):
        r = n - used
        for (even, odd, a, parity), pending in dp[used].items():
            poly = reduce_packed(pending)
            next_parity = parity ^ 1
            if next_parity:
                available = half - odd
                other_full = even == half
            else:
                available = half - even
                other_full = odd == half
            start = available if other_full else 1
            for b in range(max(1, start), available + 1):
                key = ((even, odd + b, b, 1) if next_parity
                       else (even + b, odd, b, 0))
                target = dp[used + b]
                target[key] = target.get(key, 0) + poly * factor(a, b, r)

    # The packed polynomials use y = 1+x, where x marks edges.
    total = [0] * (max_edges + 1)
    for value in dp[n].values():
        for k, c in enumerate(coefficients(value)):
            total[k] += c

    ans = [0] * (max_edges + 1)
    for k in range(n - 1, max_edges + 1):
        c = total[k] % mod
        if c:
            binom = 1
            for m in range(k, n - 2, -1):
                ans[m] += c * binom
                binom = binom * m // (k - m + 1)
    return ' '.join(str(v % mod) for v in ans[n - 1:])

def main():
    n, p = map(int, sys.stdin.buffer.read().split())
    print(solve(n, p))

if __name__ == '__main__':
    main()
