import sys
from math import comb, factorial
from struct import iter_unpack


def solve(n, mod):
    half = n // 2
    limit = n * (n - 1) // 2
    pascal = [[1]]
    for i in range(1, limit + 1):
        row = pascal[-1]
        pascal.append([1] + [(a + b) % mod for a, b in zip(row, row[1:])] + [1])

    # For adjacent layer sizes a,b, the edge generating polynomial is
    # (1+x)^C(b,2) * ((1+x)^a - 1)^b. Divide by b! for label assignment.
    # Pack coefficients into 80-bit slots for fast integer convolution.
    # With <=436 terms per product and <=450 incoming products (including the final sum),
    # reduced coefficients below 10^9 cannot cause carries between slots.
    invfac = [pow(factorial(b), -1, mod) for b in range(half + 1)]
    kernels = [[0] * (half + 1) for _ in range(half + 1)]
    for a in range(1, half + 1):
        for b in range(1, half + 1):
            inside = b * (b - 1) // 2
            top = inside + a * b
            coeff = [0] * (top - b + 1)
            for j in range(b + 1):
                w = comb(b, j) * (-1 if (b-j) & 1 else 1)
                for k, v in enumerate(pascal[inside + a*j][b:]):
                    coeff[k] += w * v
            f = invfac[b]
            kernels[a][b] = int.from_bytes(
                b''.join((v * f % mod).to_bytes(10, 'little') for v in coeff),
                'little',
            )

    # A positive last-layer size means its distance is even.
    # All polynomials are stored with the mandatory factor x^(total-1) removed.
    dp = [{} for _ in range(n)]
    dp[1][1, 1] = 1
    answer = 0
    for total in range(1, n):
        for (even, last), raw in dp[total].items():
            if not raw:
                continue
            data = raw.to_bytes(10 * ((raw.bit_length() + 79) // 80), 'little')
            value = int.from_bytes(
                b''.join(((lo + (hi << 64)) % mod).to_bytes(10, 'little')
                         for lo, hi in iter_unpack('<QH', data)),
                'little',
            )
            a = abs(last)
            ker = kernels[a]
            odd = total - even
            if last > 0:
                space = half - odd
                other = half - even
                if other == 0:
                    answer += value * ker[space]
                    continue
                for b in range(1, space + 1):
                    dest = dp[total+b]
                    key = (even, -b)
                    dest[key] = dest.get(key, 0) + value * ker[b]
            else:
                space = half - even
                other = half - odd
                if other == 0:
                    answer += value * ker[space]
                    continue
                for b in range(1, space + 1):
                    dest = dp[total+b]
                    key = (even+b, b)
                    dest[key] = dest.get(key, 0) + value * ker[b]
        dp[total].clear()

    factor = factorial(n - 1) % mod
    data = answer.to_bytes(10 * (limit - n + 2), 'little')
    return [((lo + (hi << 64)) % mod) * factor % mod
            for lo, hi in iter_unpack('<QH', data)]


if __name__ == '__main__':
    n, mod = map(int, sys.stdin.buffer.readline().split())
    print(*solve(n, mod))
