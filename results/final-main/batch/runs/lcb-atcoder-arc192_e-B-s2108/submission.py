import sys

MOD = 998244353


def main():
    w, h, l, r, d, u = map(int, sys.stdin.buffer.read().split())
    n = w + h + 4
    fact = [1] * (n + 1)
    invfact = [1] * (n + 1)
    for i in range(1, n + 1):
        fact[i] = fact[i - 1] * i % MOD
    invfact[n] = pow(fact[n], MOD - 2, MOD)
    for i in range(n, 0, -1):
        invfact[i - 1] = invfact[i] * i % MOD

    def rectangle(x, y):
        if x == 0 or y == 0:
            return 0
        # Sum (x-i)(y-j)*C(i+j,i) over all displacements.
        return (fact[x + y + 2] * invfact[x + 1] * invfact[y + 1]
                - (x + 2) - (x + 1) * y) % MOD

    def turn(width, height, edge, level):
        # Cross upward from level-1 to level at x > edge.
        # The starting x must be <= edge, so the path is not wholly on the right.
        if level == 0 or edge == width:
            return 0
        f, g, mod = fact, invfact, MOD
        b = height - level + 1
        inv_level = g[level]
        inv_b = g[b]
        total = 0
        for x in range(edge + 1, width + 1):
            prefix = (f[x + level + 1] * g[x + 1]
                      - f[x - edge + level] * g[x - edge]) * inv_level % mod
            a = width - x + 1
            suffix = f[a + b] * g[a] * inv_b % mod - 1
            total += prefix * suffix
        return total % mod

    left, right = l, w - r
    bottom, top = d, h - u
    ans = (rectangle(left, h + 1) + rectangle(right, h + 1)
           + rectangle(w + 1, bottom) + rectangle(w + 1, top))
    for x in (left, right):
        for y in (bottom, top):
            ans -= rectangle(x, y)

    # Paths not wholly in any strip first enter x>=l, y>=d
    # either from below on the right or from the left above the hole.
    ans += turn(w, h, r, d) + turn(h, w, u, l)
    print(ans % MOD)


if __name__ == "__main__":
    main()
