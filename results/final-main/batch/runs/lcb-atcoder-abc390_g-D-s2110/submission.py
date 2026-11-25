import sys

def solve():
    MOD = 998244353
    line = sys.stdin.read().strip()
    if not line:
        return
    N = int(line)
    
    # For each position j (0-indexed from left, 0 to N-1), weight is 10^(N-1-j)
    # For a number x with d digits, if it starts at position k (0-indexed from left),
    # it occupies positions k, k+1, ..., k+d-1.
    # The digit at position k+j (where j=0..d-1) has weight 10^(N-1-(k+j)).
    # 
    # For a fixed number x with d digits and digits d_0, d_1, ..., d_{d-1} (d_0 most significant):
    # If x starts at position k (0 <= k <= N-d), then:
    #   d_0 contributes d_0 * 10^(N-1-k)
    #   d_1 contributes d_1 * 10^(N-1-k-1)
    #   ...
    #   d_{d-1} contributes d_{d-1} * 10^(N-1-k-(d-1))
    #
    # Sum over k from 0 to N-d:
    #   d_0 * sum_{k=0}^{N-d} 10^(N-1-k) 
    #   + d_1 * sum_{k=0}^{N-d} 10^(N-1-k-1)
    #   + ...
    #   + d_{d-1} * sum_{k=0}^{N-d} 10^(N-1-k-(d-1))
    #
    # Let's compute sum_{k=0}^{N-d} 10^(N-1-k-j) for each j.
    # Let t = N-1-k-j. As k goes from 0 to N-d, t goes from N-1-j down to N-1-(N-d)-j = d-1-j.
    # So sum_{k=0}^{N-d} 10^(N-1-k-j) = sum_{t=d-1-j}^{N-1-j} 10^t.
    #
    # Let P[i] = sum_{t=0}^{i-1} 10^t = (10^i - 1) / 9 mod MOD.
    # Then sum_{t=a}^{b} 10^t = P[b+1] - P[a] mod MOD.
    #
    # For digit d_j (j-th digit from left, 0-indexed):
    #   weight_sum = P[N-j] - P[d-j]
    #
    # Total contribution of x = (N-d)! * sum_{j=0}^{d-1} d_j * (P[N-j] - P[d-j])
    #
    # Steps:
    # 1. Precompute powers of 10 mod MOD.
    # 2. Precompute P[i] = (10^i - 1) * inv(9) mod MOD.
    # 3. Precompute factorials.
    # 4. For each x from 1 to N, compute its contribution.
    
    pow10 = [1] * (N + 2)
    for i in range(1, N + 2):
        pow10[i] = (pow10[i-1] * 10) % MOD
    
    inv9 = pow(9, MOD-2, MOD)
    P = [0] * (N + 2)
    for i in range(1, N + 2):
        P[i] = (pow10[i] - 1) * inv9 % MOD
    
    fact = [1] * (N + 1)
    for i in range(1, N + 1):
        fact[i] = (fact[i-1] * i) % MOD
    
    total = 0
    
    for x in range(1, N + 1):
        s = str(x)
        d = len(s)
        multiplier = fact[N - d]
        
        digit_sum = 0
        for j, ch in enumerate(s):
            digit = int(ch)
            # weight_sum = P[N-j] - P[d-j]
            weight_sum = (P[N - j] - P[d - j]) % MOD
            digit_sum = (digit_sum + digit * weight_sum) % MOD
        
        contribution = (digit_sum * multiplier) % MOD
        total = (total + contribution) % MOD
    
    print(total)

if __name__ == "__main__":
    solve()
