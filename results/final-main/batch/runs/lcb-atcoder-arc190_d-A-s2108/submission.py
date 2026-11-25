import sys

def solve():
    input_data = sys.stdin.read().split()
    idx = 0
    N = int(input_data[idx]); idx += 1
    p = int(input_data[idx]); idx += 1
    
    A = []
    for i in range(N):
        row = []
        for j in range(N):
            row.append(int(input_data[idx])); idx += 1
        A.append(row)
    
    # Count zeros
    zeros = []
    for i in range(N):
        for j in range(N):
            if A[i][j] == 0:
                zeros.append((i, j))
    
    K = len(zeros)
    
    # For each entry (i,j) of the sum, we need to compute:
    # sum_B (B^p)_{ij} mod p
    #
    # Key insight: By Fermat's little theorem, for any matrix B over F_p,
    # B^p = B (mod p) is NOT true in general. However, we can use the fact that
    # the sum over all B of B^p can be computed by considering only paths that
    # use only non-zero entries from A.
    #
    # Actually, the correct approach is:
    # For each entry (i,j), the sum is:
    # sum_{paths of length p from i to j} (product of entries along the path) * (sum over all B of the product)
    #
    # For a path that uses m zero positions, the sum over B of the product is:
    # (p-1)^K * (product of non-zero entries) * (sum over the m zero positions of their values)
    # But sum_{x=1}^{p-1} x = 0 mod p, so if m >= 1, the sum is 0 mod p.
    #
    # Therefore, only paths that use NO zero positions contribute, and their contribution is:
    # (p-1)^K * (product of entries along the path) mod p
    #
    # So the answer for each (i,j) is:
    # (p-1)^K * (sum over all paths of length p from i to j using only non-zero entries of A) mod p
    #
    # But wait, we need to compute this sum modulo p. And (p-1)^K mod p = (-1)^K mod p.
    #
    # So the algorithm is:
    # 1. Create a matrix M where M[i][j] = A[i][j] if A[i][j] != 0, else 0.
    # 2. Compute M^p mod p.
    # 3. Multiply each entry by (-1)^K mod p.
    # 4. Print the result.
    
    # Create matrix with zeros replaced by 0 (they stay 0)
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
    for i in range(N):
        for j in range(N):
            print((Mp[i][j] * sign) % p, end=' ')
        print()

solve()
