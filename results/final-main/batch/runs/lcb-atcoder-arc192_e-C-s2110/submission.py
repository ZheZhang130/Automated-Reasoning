import sys

# Set recursion depth just in case, though we use iterative approach
sys.setrecursionlimit(2000000)

def solve():
    # Read input
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        parts = list(map(int, line.split()))
        W, H, L, R, D, U = parts
    except ValueError:
        return

    MOD = 998244353
    MAX_N = W + H + 10
    fact = [1] * MAX_N
    inv = [1] * MAX_N
    finv = [1] * MAX_N

    for i in range(2, MAX_N):
        fact[i] = (fact[i-1] * i) % MOD

    inv[MAX_N-1] = pow(fact[MAX_N-1], MOD - 2, MOD)
    for i in range(MAX_N-2, -1, -1):
        inv[i] = (inv[i+1] * (i+1)) % MOD

    def nCr(n, r):
        if r < 0 or r > n:
            return 0
        num = fact[n]
        den = (inv[r] * inv[n-r]) % MOD
        return (num * den) % MOD

    # G(a, b) = C(a+b+4, a+2) - (a+b+4) - (a+1)*(b+1)
    def G(a, b):
        if a < 0 or b < 0:
            return 0
        n = a + b + 4
        k = a + 2
        term1 = nCr(n, k)
        term2 = (a + b + 4) % MOD
        term3 = ((a + 1) * (b + 1)) % MOD
        res = (term1 - term2 - term3) % MOD
        return res

    # Total paths in full grid
    total = G(W, H)

    # Forbidden rectangle: x in [L, R], y in [D, U]
    # Subtract paths that start inside the forbidden rectangle
    # Start points: x in [L, R], y in [D, U]
    # For a start at (x, y), number of paths = F(W-x, H-y)
    # F(a, b) = C(a+b+2, a+1) - 1
    def F(a, b):
        if a < 0 or b < 0:
            return 0
        n = a + b + 2
        k = a + 1
        term1 = nCr(n, k)
        term2 = 1
        res = (term1 - term2) % MOD
        return res

    start_paths = 0
    for x in range(L, R + 1):
        for y in range(D, U + 1):
            start_paths = (start_paths + F(W - x, H - y)) % MOD

    # Subtract paths that enter the forbidden rectangle
    # Entry from left: (L-1, y) -> (L, y) for y in [D, U]
    # Number of such paths = F(L-1, y) * F(W-L, H-y)
    # Note: F(L-1, y) is number of paths ending at (L-1, y) from any start
    # But we need paths that end at (L-1, y) and then step to (L, y)
    # Actually, the formula is: paths ending at (L-1, y) * 1 (the step) * paths starting at (L, y)
    # Paths starting at (L, y) = F(W-L, H-y)
    # Paths ending at (L-1, y) = F(L-1, y)
    # So product is correct.
    
    entry_left = 0
    if L > 0:
        for y in range(D, U + 1):
            entry_left = (entry_left + F(L - 1, y) * F(W - L, H - y)) % MOD

    # Entry from below: (x, D-1) -> (x, D) for x in [L, R]
    # Number of such paths = F(x, D-1) * F(W-x, H-D)
    entry_bottom = 0
    if D > 0:
        for x in range(L, R + 1):
            entry_bottom = (entry_bottom + F(x, D - 1) * F(W - x, H - D)) % MOD

    # Total forbidden paths = start_paths + entry_left + entry_bottom
    forbidden = (start_paths + entry_left + entry_bottom) % MOD

    ans = (total - forbidden) % MOD
    print(ans)

if __name__ == "__main__":
    solve()
