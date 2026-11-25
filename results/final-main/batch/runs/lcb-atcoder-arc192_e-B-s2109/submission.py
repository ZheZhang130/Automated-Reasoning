import sys
from array import array

MOD = 998244353


def main():
    w, h, l, r, d, u = map(int, sys.stdin.buffer.read().split())
    n = w + h + 4
    fact = array('I', [1]) * (n + 1)
    inv = array('I', [1]) * (n + 1)
    value = 1
    for i in range(2, n + 1):
        value = value * i % MOD
        fact[i] = value
    value = pow(value, MOD - 2, MOD)
    inv[n] = value
    for i in range(n, 1, -1):
        value = value * i % MOD
        inv[i - 1] = value

    def prefix(a, b):
        if a < 0 or b < 0:
            return 0
        return (fact[a + b + 4] * inv[a + 2] * inv[b + 2]
                - a - b - 4 - (a + 1) * (b + 1)) % MOD

    ans = prefix(w, h)
    # Paths starting in the hole: sum unrestricted suffix counts.
    a, b, c, e = w - r, w - l, h - u, h - d
    ans -= prefix(b, e) - prefix(a - 1, e) - prefix(b, c - 1) + prefix(a - 1, c - 1)

    def entering(width, height, left, low, high):
        # First entry is from (left-1, y) into (left, y).
        if left == 0:
            return 0
        pre = inv[left]
        post = inv[width - left + 1]
        total = 0
        for y in range(low, high + 1):
            z = height - y
            p = fact[left + y + 1] * inv[y + 1] * pre % MOD - 1
            q = fact[width - left + z + 2] * inv[z + 1] * post % MOD - 1
            total += p * q
        return total

    ans -= entering(w, h, l, d, u)
    ans -= entering(h, w, d, l, r)
    print(ans % MOD)


if __name__ == '__main__':
    main()
