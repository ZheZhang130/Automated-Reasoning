import sys

def solve():
    data = sys.stdin.read().split()
    it = iter(data)
    N = int(next(it))
    p = int(next(it))
    A = [[int(next(it)) for _ in range(N)] for _ in range(N)]
    
    # Count zeros
    zeros = []
    for i in range(N):
        for j in range(N):
            if A[i][j] == 0:
                zeros.append((i, j))
    K = len(zeros)
    
    # Create matrix with zeros as 0
    M = [row[:] for row in A]
    
    # Compute M^p mod p
    def mat_mul(M1, M2):
        N = len(M1)
        res = [[0]*N for _ in range(N)]
        for i in range(N):
            for k in range(N):
                if M1[i][k] == 0:
                    continue
                for j in range(N):
                    res[i][j] = (res[i][j] + M1[i][k] * M2[k][j]) % p
        return res
    
    def mat_pow(M, exp):
        N = len(M)
        res = [[0]*N for _ in range(N)]
        for i in range(N):
            res[i][i] = 1
        base = [row[:] for row in M]
        while exp > 0:
            if exp & 1:
                res = mat_mul(res, base)
            base = mat_mul(base, base)
            exp >>= 1
        return res
    
    Mp = mat_pow(M, p)
    
    # Multiply by (-1)^K mod p
    sign = 1 if K % 2 == 0 else p - 1
    
    # For p=2, the only non-zero value is 1, so we just fill zeros with 1
    if p == 2:
        for i in range(N):
            for j in range(N):
                if A[i][j] == 0:
                    A[i][j] = 1
        Mp = mat_pow(A, p)
        for row in Mp:
            print(*(row))
        return
    
    # For p > 2, we need to add corrections for walks that use the same zero position multiple times
    # For p=3, p-1=2. A walk of length 3 can use the same zero position twice.
    # If a zero position (r,c) is used twice in a walk, the sum over its values is sum_{x=1}^{p-1} x^2 = -1 mod p.
    # So the contribution is (-1) * (product of other edges).
    # Total: (-1)^K * (-1) * (product of other edges) = (-1)^{K+1} * (product of other edges).
    
    if p == 3:
        # Create a matrix of replacement positions
        is_replacement = [[A[i][j] == 0 for j in range(N)] for i in range(N)]
        
        # For p=3, compute corrections for walks using the same zero position twice
        correction = [[0]*N for _ in range(N)]
        
        # For each zero position (r,c), consider walks that use it twice
        for r in range(N):
            for c in range(N):
                if not is_replacement[r][c]:
                    continue
                # Walk: i -> r -> c -> j (uses (r,c) once)
                # Walk: i -> r -> r -> j (uses (r,c) twice? No, (r,r) is different)
                # Actually, we need to find walks where (r,c) appears twice.
                # This can happen as: i -> r -> c -> r -> c -> j (length 5, too long)
                # Or: i -> r -> c -> j where one of (i,r) or (c,j) is also (r,c)
                # i.e., i=r or j=c
                
                # Case: i=r, so walk is r -> r -> c -> j, using (r,c) at positions 1 and 2
                # The edges are (r,r), (r,c), (c,j). (r,c) is used once.
                # Wait, I need to think about this differently.
                
                # For a walk of length 3: v0 -> v1 -> v2 -> v3
                # The edges are (v0,v1), (v1,v2), (v2,v3).
                # If (r,c) appears twice, then either:
                # - (v0,v1) = (r,c) and (v1,v2) = (r,c), so v0=r, v1=c, v2=r, v3=j
                #   This gives walk r -> c -> r -> j
                # - (v1,v2) = (r,c) and (v2,v3) = (r,c), so v0=i, v1=r, v2=c, v3=r
                #   This gives walk i -> r -> c -> r
                # - (v0,v1) = (r,c) and (v2,v3) = (r,c), so v0=r, v1=c, v2=r, v3=c
                #   This gives walk r -> c -> r -> c
                
                # For each case, the sum over the two (r,c) edges is sum_{x=1}^{p-1} x^2 = -1 mod p.
                # The third edge is fixed.
                
                # Case 1: r -> c -> r -> j
                # Edges: (r,c), (c,r), (r,j). (r,c) appears twice.
                # Contribution: (-1) * A[c][r] * A[r][j]
                for j in range(N):
                    if not is_replacement[r][j]:  # (r,j) is fixed
                        correction[r][j] = (correction[r][j] + A[c][r] * A[r][j]) % p
                
                # Case 2: i -> r -> c -> r
                # Edges: (i,r), (r,c), (c,r). (r,c) appears twice.
                # Contribution: (-1) * A[i][r] * A[c][r]
                for i in range(N):
                    if not is_replacement[i][r]:  # (i,r) is fixed
                        correction[i][r] = (correction[i][r] + A[i][r] * A[c][r]) % p
                
                # Case 3: r -> c -> r -> c
                # Edges: (r,c), (c,r), (r,c). (r,c) appears twice.
                # Contribution: (-1) * A[c][r]
                # But this is a walk from r to c, so correction[r][c]
                correction[r][c] = (correction[r][c] + A[c][r]) % p
        
        # Add corrections with sign (-1)^{K+1}
        sign_corr = 1 if (K + 1) % 2 == 0 else p - 1
        for i in range(N):
            for j in range(N):
                Mp[i][j] = (Mp[i][j] + sign_corr * correction[i][j]) % p
    
    for row in Mp:
        print(*(row))

solve()
