import sys

def solve():
    # Read N from standard input
    try:
        input_data = sys.stdin.read().strip()
        if not input_data:
            return
        N = int(input_data)
    except ValueError:
        return

    MOD = 998244353

    # Precompute factorials
    fact = [1] * (N + 1)
    for i in range(1, N + 1):
        fact[i] = (fact[i-1] * i) % MOD

    # Group numbers by digit length
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

    # Compute R(t) = product_d (1 + w_d * t)
    R = [0] * (N + 1)
    R[0] = 1
    
    for _, _, _, w in groups:
        new_R = [0] * (len(R) + 1)
        for i in range(len(R)):
            new_R[i] = (new_R[i] + R[i]) % MOD
            if i + 1 < len(new_R):
                new_R[i+1] = (new_R[i+1] + R[i] * w) % MOD
        R = new_R
    
    # Compute the answer
    total = 0
    
    for _, c, s, w in groups:
        # Compute R(t) / (1 + w*t)
        Q_div = [0] * (N + 1)
        Q_div[0] = R[0]
        
        for i in range(1, N + 1):
            Q_div[i] = (R[i] - w * Q_div[i-1]) % MOD
        
        # Add s * sum_{k=0}^{N-1} Q_div[k] * k! * (N-1-k)!
        factor = s % MOD
        for k in range(N):
            term = (Q_div[k] * fact[k] * fact[N - 1 - k]) % MOD
            total = (total + factor * term) % MOD
    
    print(total % MOD)

if __name__ == "__main__":
    solve()
