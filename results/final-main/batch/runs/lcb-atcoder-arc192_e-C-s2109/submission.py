import sys

def solve():
    # Read input
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    W = int(input_data[0])
    H = int(input_data[1])
    L = int(input_data[2])
    R = int(input_data[3])
    D = int(input_data[4])
    U = int(input_data[5])

    MOD = 998244353
    MAX_N = W + H + 10
    fact = [1] * MAX_N
    inv = [1] * MAX_N
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
        term1 = nCr(a + b + 4, a + 2)
        term2 = (a + b + 4) % MOD
        term3 = ((a + 1) * (b + 1)) % MOD
        res = (term1 - term2 - term3) % MOD
        return res

    # Total paths in full grid
    total = G(W, H)

    # Forbidden rectangle: x in [L, R], y in [D, U]
    # Subtract paths that start inside the forbidden rectangle
    # Start x in [L, R], start y in [D, U]
    # Number of such starts: (R - L + 1) * (U - D + 1)
    # For each start (sx, sy), number of paths is F(W-sx, H-sy)
    # F(a, b) = C(a+b+2, a+1) - 1
    # Sum over sx in [L, R], sy in [D, U] of (C(W-sx + H-sy + 2, W-sx + 1) - 1)
    # = Sum C(...) - (R-L+1)*(U-D+1)
    
    # Let i = W - sx, j = H - sy
    # sx = W - i, sy = H - j
    # sx in [L, R] => W - i in [L, R] => i in [W-R, W-L]
    # sy in [D, U] => H - j in [D, U] => j in [H-U, H-D]
    
    i_min, i_max = W - R, W - L
    j_min, j_max = H - U, H - D
    
    sum_C = 0
    for i in range(i_min, i_max + 1):
        for j in range(j_min, j_max + 1):
            sum_C = (sum_C + nCr(i + j + 2, i + 1)) % MOD
    
    num_starts = ((R - L + 1) * (U - D + 1)) % MOD
    subtract_starts = (sum_C - num_starts) % MOD

    # Subtract paths that enter the forbidden rectangle
    # Entry from left: x = L-1 -> x = L, y in [D, U]
    # Entry from bottom: y = D-1 -> y = D, x in [L, R]
    
    # Entry from left: step (L-1, y) -> (L, y)
    # Prefix: paths from any start to (L-1, y)
    # Suffix: paths from (L, y) to any end
    # Prefix count: F(L-1, y)
    # Suffix count: F(W-L, H-y)
    # Note: F(a,b) = C(a+b+2, a+1) - 1
    
    subtract_left = 0
    if L > 0:
        for y in range(D, U + 1):
            # Prefix: to (L-1, y)
            # Suffix: from (L, y)
            # F(L-1, y) = C((L-1)+y+2, (L-1)+1) - 1 = C(L+y+1, L) - 1
            # F(W-L, H-y) = C((W-L)+(H-y)+2, (W-L)+1) - 1 = C(W+H-L-y+2, W-L+1) - 1
            # But we need to be careful: the formula F(a,b) is for paths from (0,0) to (a,b) in a full grid
            # Here, prefix is from any start to (L-1, y), which is F(L-1, y)
            # Suffix is from (L, y) to any end, which is F(W-L, H-y)
            
            # Actually, let's re-derive:
            # F(a, b) = number of paths from (0,0) to (a,b) in full grid, starting from any point? 
            # No, F(a,b) as defined in the problem sketch is: number of paths ending at (a,b) with any starting point.
            # That is equivalent to: number of paths from any start to (a,b) in full grid.
            # By symmetry, number of paths from (x,y) to any end is F(W-x, H-y).
            
            # So for entry from left at (L, y):
            # Prefix: paths from any start to (L-1, y) = F(L-1, y)
            # Suffix: paths from (L, y) to any end = F(W-L, H-y)
            
            a = L - 1
            b = y
            prefix = nCr(a + b + 2, a + 1) - 1
            a2 = W - L
            b2 = H - y
            suffix = nCr(a2 + b2 + 2, a2 + 1) - 1
            
            subtract_left = (subtract_left + prefix * suffix) % MOD
    
    subtract_bottom = 0
    if D > 0:
        for x in range(L, R + 1):
            # Entry from bottom: (x, D-1) -> (x, D)
            # Prefix: paths from any start to (x, D-1) = F(x, D-1)
            # Suffix: paths from (x, D) to any end = F(W-x, H-D)
            
            a = x
            b = D - 1
            prefix = nCr(a + b + 2, a + 1) - 1
            a2 = W - x
            b2 = H - D
            suffix = nCr(a2 + b2 + 2, a2 + 1) - 1
            
            subtract_bottom = (subtract_bottom + prefix * suffix) % MOD
    
    subtract_entries = (subtract_left + subtract_bottom) % MOD
    
    # Also subtract paths that start inside and also enter? 
    # The problem says: "Every path that visits the forbidden rectangle either starts there or has a unique first entry"
    # So we subtract:
    # 1. Paths that start inside (already done: subtract_starts)
    # 2. Paths that enter from left (subtract_left)
    # 3. Paths that enter from bottom (subtract_bottom)
    # But wait: if a path starts inside, it doesn't "enter" from left or bottom.
    # And if a path enters from left or bottom, it doesn't start inside.
    # So these are disjoint cases.
    
    # However, we must be careful: the subtract_starts counts paths that start inside.
    # The subtract_entries counts paths that enter from left or bottom.
    # These are disjoint, so we can simply subtract both.
    
    # But wait: the problem says "unique first entry". 
    # If a path starts inside, it has no first entry.
    # If a path enters from left, it has first entry from left.
    # If a path enters from bottom, it has first entry from bottom.
    # These are all the cases for paths that visit the forbidden rectangle.
    
    # So total forbidden = subtract_starts + subtract_entries
    
    forbidden = (subtract_starts + subtract_entries) % MOD
    
    ans = (total - forbidden) % MOD
    print(ans)

solve()
