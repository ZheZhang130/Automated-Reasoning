import sys

MOD = 998244353

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    W, H, L, R, D, U = map(int, data)

    # Precompute factorials
    N = W + H + 10
    fact = [1] * (N + 1)
    inv = [1] * (N + 1)
    for i in range(1, N + 1):
        fact[i] = (fact[i-1] * i) % MOD
    inv[N] = pow(fact[N], MOD - 2, MOD)
    for i in range(N - 1, -1, -1):
        inv[i] = (inv[i+1] * (i + 1)) % MOD

    def C(n, k):
        if k < 0 or k > n:
            return 0
        return fact[n] * inv[k] % MOD * inv[n-k] % MOD

    # F(a,b) = C(a+b+2, a+1) - 1
    def F(a, b):
        return (C(a + b + 2, a + 1) - 1 + MOD) % MOD

    # G(a,b) = C(a+b+4, a+2) - (a+b+4) - (a+1)*(b+1)
    def G(a, b):
        if a < 0 or b < 0:
            return 0
        term1 = C(a + b + 4, a + 2)
        term2 = (a + b + 4)
        term3 = ((a + 1) * (b + 1)) % MOD
        return (term1 - term2 - term3 + MOD) % MOD

    # Total paths in full grid
    ans = G(W, H)

    # Subtract paths that enter forbidden region
    # Forbidden: x in [L, R], y in [D, U]
    # Entry from left: x = L-1 -> L, y in [D, U]
    if L > 0:
        for y in range(D, U + 1):
            term = F(L - 1, y) * F(W - L, H - y)
            ans = (ans - term + MOD) % MOD

    # Entry from below: y = D-1 -> D, x in [L, R]
    if D > 0:
        for x in range(L, R + 1):
            term = F(x, D - 1) * F(W - x, H - D)
            ans = (ans - term + MOD) % MOD

    print(ans)

solve()
