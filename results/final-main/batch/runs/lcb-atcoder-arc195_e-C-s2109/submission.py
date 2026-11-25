import sys

# Set recursion limit just in case, though we don't use recursion
sys.setrecursionlimit(200000)

def solve():
    # Read all input from stdin
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    
    try:
        N = int(next(iterator))
        Q = int(next(iterator))
        
        # A is 1-indexed in problem, but we'll use 0-indexed list where index i corresponds to vertex i+2
        # A_2 corresponds to index 0, A_3 to index 1, ..., A_N to index N-2
        A = []
        for _ in range(N - 1):
            A.append(int(next(iterator)))
            
        # Precompute modular inverse for 1 to N
        MOD = 998244353
        
        # Linear precomputation of modular inverses
        inv = [1] * (N + 1)
        inv[1] = 1
        for i in range(2, N + 1):
            inv[i] = (MOD - (MOD // i) * inv[MOD % i] % MOD) % MOD
            
        # Precompute factorials
        fact = [1] * (N + 1)
        for i in range(2, N + 1):
            fact[i] = (fact[i-1] * i) % MOD
            
        F = fact[N - 1]  # (N-1)!
        
        # Precompute M and B arrays
        # M[k] corresponds to vertex k (1-indexed)
        # B[k] corresponds to vertex k (1-indexed)
        # We'll use 1-indexed arrays for convenience
        
        M = [0] * (N + 1)
        B = [0] * (N + 1)
        
        # M[1] = 0, B[1] = 0 (already set)
        
        # For k from 2 to N:
        # A_k is A[k-2] in our 0-indexed A list
        # R_k = (k-1)*A_k + T_{k-1}/(k-1)
        # T_k = T_{k-1} + 2*R_k
        # M_k = R_k / k
        # B_k = B_{k-1} + A_k / k
        
        # We need to track T_k
        T = 0
        
        for k in range(2, N + 1):
            # A_k is A[k-2]
            Ak = A[k - 2]
            
            # R_k = (k-1)*Ak + T/(k-1)
            term1 = ((k - 1) * Ak) % MOD
            term2 = (T * inv[k - 1]) % MOD
            Rk = (term1 + term2) % MOD
            
            # T_k = T_{k-1} + 2*R_k
            T = (T + 2 * Rk) % MOD
            
            # M_k = R_k / k
            Mk = (Rk * inv[k]) % MOD
            M[k] = Mk
            
            # B_k = B_{k-1} + Ak / k
            Bk = (B[k - 1] + (Ak * inv[k]) % MOD) % MOD
            B[k] = Bk
            
        # Process queries
        results = []
        for _ in range(Q):
            u = int(next(iterator))
            v = int(next(iterator))
            
            # Expected distance = A_v + M_u + B_{v-1} - B_u
            # A_v is A[v-2]
            Av = A[v - 2]
            
            Mu = M[u]
            Bv_minus_1 = B[v - 1]
            Bu = B[u]
            
            expected = (Av + Mu + Bv_minus_1 - Bu) % MOD
            expected = (expected + MOD) % MOD  # Ensure non-negative
            
            ans = (expected * F) % MOD
            results.append(str(ans))
            
        print('\n'.join(results))
        
    except StopIteration:
        pass

if __name__ == '__main__':
    solve()
