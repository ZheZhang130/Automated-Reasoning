import sys

def solve():
    data = sys.stdin.read().split()
    it = iter(data)
    N = int(next(it))
    Q = int(next(it))
    A = [int(next(it)) for _ in range(N-1)]
    MOD = 998244353
    
    fact = [1]*(N+1)
    for i in range(2, N+1):
        fact[i] = (fact[i-1]*i) % MOD
    
    inv = [1]*(N+1)
    inv[N] = pow(fact[N], MOD-2, MOD)
    for i in range(N-1, 1, -1):
        inv[i] = (inv[i+1]*(i+1)) % MOD
    
    inv_fact = [1]*(N+1)
    for i in range(1, N+1):
        inv_fact[i] = (inv_fact[i-1]*inv[i]) % MOD
    
    S = [0]*(N+1)
    for i in range(N-1):
        S[i+1] = (S[i] + A[i]) % MOD
    
    total_perms = fact[N-1]
    
    out = []
    for _ in range(Q):
        u = int(next(it))
        v = int(next(it))
        w_sum = (S[v-1] - S[u-1]) % MOD
        k = v - u
        term = (inv_fact[k] * total_perms) % MOD
        ans = (w_sum * term) % MOD
        out.append(str(ans))
    print('\n'.join(out))

if __name__ == '__main__':
    solve()
