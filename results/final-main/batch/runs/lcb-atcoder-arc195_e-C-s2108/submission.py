import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    N = int(next(iterator))
    Q = int(next(iterator))
    
    A = [0] * (N + 1)
    for i in range(2, N + 1):
        A[i] = int(next(iterator))
    
    MOD = 998244353
    
    # Precompute modular inverses for 1 to N
    inv = [1] * (N + 1)
    inv[1] = 1
    for i in range(2, N + 1):
        inv[i] = (MOD - (MOD // i) * inv[MOD % i] % MOD) % MOD
    
    # Precompute factorials
    fact = [1] * (N + 1)
    for i in range(2, N + 1):
        fact[i] = (fact[i-1] * i) % MOD
    
    F = fact[N-1]  # (N-1)!
    
    # Precompute M and B arrays
    # M[k] = average expected distance from vertex k to the first k vertices (including itself)
    # B[k] = prefix sum of A[i]/i for i from 2 to k
    M = [0] * (N + 1)
    B = [0] * (N + 1)
    
    # For k=1, M[1]=0, B[1]=0
    # For k from 2 to N:
    #   R_k = (k-1)*A[k] + T_{k-1}/(k-1)
    #   T_k = T_{k-1} + 2*R_k
    #   M[k] = R_k / k
    #   B[k] = B[k-1] + A[k]/k
    
    T = 0
    for k in range(2, N + 1):
        term1 = (k - 1) * A[k] % MOD
        term2 = (T * inv[k-1]) % MOD
        R_k = (term1 + term2) % MOD
        M[k] = (R_k * inv[k]) % MOD
        
        term3 = (A[k] * inv[k]) % MOD
        B[k] = (B[k-1] + term3) % MOD
        
        T = (T + 2 * R_k) % MOD
    
    # Process queries
    results = []
    for _ in range(Q):
        u = int(next(iterator))
        v = int(next(iterator))
        
        # Expected distance = A[v] + M[u] + B[v-1] - B[u]
        expected = (A[v] + M[u] + B[v-1] - B[u]) % MOD
        ans = (expected * F) % MOD
        results.append(str(ans))
    
    print('\n'.join(results))

if __name__ == "__main__":
    solve()
