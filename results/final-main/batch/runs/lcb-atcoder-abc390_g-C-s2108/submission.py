import sys

def solve():
    MOD = 998244353
    
    # Read N
    input_data = sys.stdin.read().strip()
    if not input_data:
        return
    N = int(input_data)
    
    if N == 1:
        print(1)
        return

    # Precompute factorials
    fact = [1] * (N + 1)
    for i in range(2, N + 1):
        fact[i] = (fact[i-1] * i) % MOD
    
    # Precompute modular inverses for 1..N-1
    inv = [0] * N
    inv[1] = 1
    for i in range(2, N):
        inv[i] = (MOD - (MOD // i) * inv[MOD % i] % MOD) % MOD
    
    # Group numbers by digit length
    # Groups: (digit_len, count, sum_of_values, weight=10^digit_len)
    groups = []
    d = 1
    start = 1
    while start <= N:
        end = min(N, start * 10 - 1)
        count = end - start + 1
        # Sum of arithmetic progression: count * (start + end) // 2
        s = (count * (start + end)) // 2
        w = pow(10, d, MOD)
        groups.append((d, count, s % MOD, w))
        start = end + 1
        d += 1
    
    # For each group d, we compute the contribution
    # For a number x in group d, if there are k digits after it, x contributes x * w^k
    # 
    # The key insight: for each group d, we need to compute:
    # s_d * sum over all permutations of w_d^(total digits after x for x in group d)
    # 
    # Using generating functions:
    # R(t) = product over all groups j of (1 + c_j * t^j)
    # But this is not quite right. Let me reconsider.
    
    # Actually, let's think about it more carefully:
    # For each group j, we have c_j numbers, each contributing j digits.
    # When we choose a subset of numbers to be after x, the total digits is the sum of their digit lengths.
    # 
    # The generating function for choosing numbers from group j is:
    # (1 + t^j)^(c_j) = sum over k=0 to c_j: binom(c_j, k) * t^(k*j)
    # 
    # So R(t) = product over j of (1 + t^j)^(c_j)
    # 
    # For a number x in group d, we need to divide by (1 + t^d) to exclude x itself.
    # 
    # Let's compute R(t) first:
    deg = N - 1
    R = [0] * (deg + 1)
    R[0] = 1
    
    for d, c, _, _ in groups:
        # Multiply by (1 + t^d)^c
        new_poly = [0] * (deg + 1)
        for j in range(min(c, deg // d + 1)):
            if j == 0:
                coeff = 1
            else:
                coeff = coeff * (c - j + 1) % MOD
                coeff = coeff * inv[j] % MOD
            new_poly[j * d] = coeff
        
        new_R = [0] * (len(R) + len(new_poly) - 1)
        for i in range(len(R)):
            for j in range(len(new_poly)):
                if i + j <= deg:
                    new_R[i + j] = (new_R[i + j] + R[i] * new_poly[j]) % MOD
        R = new_R[:deg + 1]
    
    # Now compute the answer
    ans = 0
    for d, c, s, w in groups:
        # Compute P(t) = R(t) / (1 + t^d)
        P = [0] * (deg + 1)
        P[0] = R[0]
        for k in range(1, deg + 1):
            if k % d == 0:
                P[k] = (R[k] - P[k - d]) % MOD
            else:
                P[k] = R[k]
        
        # Contribution: s * sum over k=0 to N-1: P[k] * w^k * k! * (N-1-k)!
        term = 0
        for k in range(deg + 1):
            term = (term + P[k] * w % MOD * fact[k] % MOD * fact[N - 1 - k]) % MOD
        ans = (ans + s * term) % MOD
    
    print(ans)

if __name__ == "__main__":
    solve()
