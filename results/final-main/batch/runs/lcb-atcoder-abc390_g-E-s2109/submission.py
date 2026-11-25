import sys

def solve():
    n = int(sys.stdin.readline().strip())
    MOD = 998244353
    
    # Precompute powers of 10
    pow10 = [1] * (n + 1)
    for i in range(1, n + 1):
        pow10[i] = (pow10[i-1] * 10) % MOD
    
    # Precompute prefix sums of powers of 10
    prefix_pow10 = [0] * (n + 1)
    current = 0
    for i in range(n + 1):
        current = (current + pow10[i]) % MOD
        prefix_pow10[i] = current
    
    # Precompute factorials
    fact = [1] * (n + 1)
    for i in range(2, n + 1):
        fact[i] = (fact[i-1] * i) % MOD
    
    # Precompute inverse factorials
    inv_fact = [1] * (n + 1)
    inv_fact[n] = pow(fact[n], MOD - 2, MOD)
    for i in range(n - 1, -1, -1):
        inv_fact[i] = (inv_fact[i+1] * (i + 1)) % MOD
    
    # Group numbers by their digit length
    groups = {}
    for x in range(1, n + 1):
        s = str(x)
        dlen = len(s)
        if dlen not in groups:
            groups[dlen] = []
        groups[dlen].append(x)
    
    # For each digit length dlen, compute the sum of 10^shift for all possible shifts
    # The shift depends on the total number of digits of numbers placed after x.
    # Let's think differently.
    # Total sum = sum over all permutations P of f(P)
    # f(P) = sum_{k=0}^{n-1} digit(P[k]) * 10^(n-1-k)
    # But P[k] is a number, not a digit. The number P[k] has multiple digits.
    # Actually, the problem says: "Let T be the decimal representation of A_i without leading zeros. Append T to the end of S."
    # So if we place number x at position k, then the digits of x are appended starting at position k.
    # This means the first digit of x goes to position k, the second to k+1, etc.
    # So for a fixed number x, and for each digit d of x at offset p (0-indexed from left of x),
    # this digit d is placed at global position k+p when x is placed at position k.
    # The power of 10 is n-1-(k+p).
    # x can be placed at position k such that k+p <= n-1, i.e., k <= n-1-p.
    # Also, x must fit, so k <= n - len(x).
    # Actually, the constraint is that the entire x fits, so k <= n - len(x).
    # But also, the digit at offset p must be within the valid range, so k+p <= n-1, i.e., k <= n-1-p.
    # So k <= min(n - len(x), n-1-p).
    # But since p < len(x), we have n-1-p > n-len(x) when len(x) > 1? Let's check:
    # n-1-p - (n-len(x)) = len(x) - 1 - p >= 0 since p <= len(x)-1.
    # So n-1-p >= n-len(x). Thus k <= n-len(x) is the tighter constraint.
    # So k ranges from 0 to n-len(x).
    # For each such k, the contribution of digit d is d * 10^(n-1-(k+p)).
    # Sum over k from 0 to n-len(x): d * 10^(n-1-p) * sum_{k=0}^{n-len(x)} 10^(-k).
    # But we are working modulo MOD, and we can compute the sum of powers directly.
    # Actually, let's change the exponent.
    # We want sum_{k=0}^{n-len(x)} 10^(n-1-(k+p)) = 10^(n-1-p) * sum_{k=0}^{n-len(x)} 10^(-k).
    # But 10^(-k) mod MOD is (inv10)^k.
    # So we need the inverse of 10 mod MOD.
    
    inv10 = pow(10, MOD - 2, MOD)
    
    # Precompute powers of inv10
    inv10_pow = [1] * (n + 1)
    for i in range(1, n + 1):
        inv10_pow[i] = (inv10_pow[i-1] * inv10) % MOD
    
    # Precompute prefix sums of inv10_pow
    prefix_inv10_pow = [0] * (n + 1)
    current = 0
    for i in range(n + 1):
        current = (current + inv10_pow[i]) % MOD
        prefix_inv10_pow[i] = current
    
    total = 0
    fact_n_minus_1 = fact[n-1]
    
    for x in range(1, n + 1):
        s = str(x)
        length = len(s)
        for idx, d_char in enumerate(s):
            d = int(d_char)
            p = idx  # offset from the start of x
            # k ranges from 0 to n-length
            # Contribution = d * 10^(n-1-p) * sum_{k=0}^{n-length} 10^(-k)
            # = d * 10^(n-1-p) * prefix_inv10_pow[n-length]
            # But wait, we need to be careful with the exponent.
            # 10^(n-1-p) * 10^(-k) = 10^(n-1-p-k).
            # So sum_{k=0}^{n-length} 10^(n-1-p-k) = sum_{j=n-1-p-(n-length)}^{n-1-p} 10^j
            # = sum_{j=len(x)-1-p}^{n-1-p} 10^j
            # = prefix_pow10[n-1-p] - prefix_pow10[len(x)-1-p-1]
            # But we need to handle the case when len(x)-1-p-1 < 0.
            
            t_max = n - 1 - p
            t_min = length - 1 - p
            if t_min < 0:
                t_min = 0
            sum_pow = (prefix_pow10[t_max] - prefix_pow10[t_min - 1]) % MOD
            if sum_pow < 0:
                sum_pow += MOD
            contribution = (d * fact_n_minus_1 * sum_pow) % MOD
            total = (total + contribution) % MOD
    
    print(total)

if __name__ == "__main__":
    solve()
