import sys

def solve():
    MOD = 998244353
    
    # Read N from stdin
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        N = int(line)
    except ValueError:
        return

    if N == 1:
        print(1)
        return

    # Precompute factorials and inverse factorials
    fact = [1] * N
    inv_fact = [1] * N
    for i in range(1, N):
        fact[i] = (fact[i-1] * i) % MOD
    
    inv_fact[N-1] = pow(fact[N-1], MOD - 2, MOD)
    for i in range(N-2, -1, -1):
        inv_fact[i] = (inv_fact[i+1] * (i + 1)) % MOD

    # Precompute modular inverses for 1..N
    inv = [0] * (N + 1)
    inv[1] = 1
    for i in range(2, N + 1):
        inv[i] = (MOD - (MOD // i) * inv[MOD % i] % MOD) % MOD

    # Group numbers by digit length
    # Groups: (digit_len, count, sum_of_values, weight=10^digit_len)
    groups = []
    current_len = 1
    current_count = 0
    current_sum = 0
    
    for x in range(1, N + 1):
        if x == 10 ** current_len:
            if current_count > 0:
                groups.append((current_len, current_count, current_sum, pow(10, current_len, MOD)))
            current_len += 1
            current_count = 0
            current_sum = 0
        current_count += 1
        current_sum = (current_sum + x) % MOD
    
    if current_count > 0:
        groups.append((current_len, current_count, current_sum, pow(10, current_len, MOD)))

    # Compute Q(t) coefficients: Q(t) = product over groups d of (1 + w_d * t)^(c_d)
    q = [1]  # q[0] = 1
    for _, c, _, w in groups:
        # Multiply current q by (1 + w*t)^c
        # Compute coefficients of (1 + w*t)^c using binomial expansion
        # (1 + w*t)^c = sum_{i=0}^c binom(c, i) * w^i * t^i
        
        # Compute binom(c, i) for i=0..c
        # binom(c, 0) = 1
        # binom(c, i) = binom(c, i-1) * (c - i + 1) / i
        
        pw_w = 1
        p = [0] * (c + 1)
        p[0] = 1
        for i in range(1, c + 1):
            pw_w = pw_w * w % MOD
            # binom(c, i) = binom(c, i-1) * (c - i + 1) * inv(i)
            binom_prev = p[i-1]
            binom_curr = binom_prev * (c - i + 1) % MOD * inv[i] % MOD
            p[i] = binom_curr * pw_w % MOD
        
        # Convolve q and p
        new_q = [0] * (len(q) + len(p) - 1)
        for i in range(len(q)):
            for j in range(len(p)):
                new_q[i + j] = (new_q[i + j] + q[i] * p[j]) % MOD
        q = new_q

    # Now compute R(t) = product_d (1 + w_d * t)
    r = [1]
    for _, _, _, w in groups:
        # Multiply r by (1 + w*t)
        new_r = [0] * (len(r) + 1)
        for i in range(len(r)):
            new_r[i] = (new_r[i] + r[i]) % MOD
            if i + 1 < len(new_r):
                new_r[i + 1] = (new_r[i + 1] + r[i] * w) % MOD
        r = new_r

    # Now compute H(t) = sum_d c_d * w_d * R(t) / (1 + w_d * t)
    # We need h up to degree N-1
    h = [0] * N
    for _, c, s, w in groups:
        # Compute R(t) / (1 + w*t)
        # Let this be b(t) = sum b_i t^i
        # Then b(t) * (1 + w*t) = R(t)
        # b_i + w * b_{i-1} = r_i  =>  b_i = r_i - w * b_{i-1}
        
        # R(t) has degree sum(c_d) - 1 = N - 1
        # So r has length N (indices 0 to N-1)
        # We need b up to degree N-1 as well
        
        b = [0] * N
        b[0] = r[0]  # r[0] should be 1
        for i in range(1, len(r)):
            b[i] = (r[i] - w * b[i-1]) % MOD
        
        # Multiply by c * s
        factor = c * s % MOD
        for i in range(len(b)):
            h[i] = (h[i] + factor * b[i]) % MOD

    # Now compute answer = sum_{i=0}^{N-1} h[i] * i! * (N-1-i)!
    ans = 0
    for i in range(N):
        term = h[i] * fact[i] % MOD * inv_fact[N - 1 - i] % MOD
        ans = (ans + term) % MOD

    print(ans)

if __name__ == "__main__":
    solve()
