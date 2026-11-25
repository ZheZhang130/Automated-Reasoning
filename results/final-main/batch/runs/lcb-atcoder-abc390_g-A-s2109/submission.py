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
    
    total = 0
    fact_n_minus_1 = fact[n-1]
    
    for x in range(1, n + 1):
        s = str(x)
        length = len(s)
        for idx, d_char in enumerate(s):
            d = int(d_char)
            p = idx  # offset from the start of x
            # When x is placed at position k (0-indexed), the digit at offset p
            # goes to global position k+p, with power n-1-(k+p).
            # k ranges from 0 to n-length.
            # So power t = n-1-(k+p) ranges from n-1-p down to n-1-(n-length+p) = length-1-p.
            t_min = length - 1 - p
            t_max = n - 1 - p
            # Sum of 10^t for t from t_min to t_max
            if t_min <= t_max:
                sum_pow = (prefix_pow10[t_max] - prefix_pow10[t_min - 1]) % MOD
                if sum_pow < 0:
                    sum_pow += MOD
                contribution = (d * fact_n_minus_1 * sum_pow) % MOD
                total = (total + contribution) % MOD
    
    print(total)

if __name__ == "__main__":
    solve()
