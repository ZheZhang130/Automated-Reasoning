import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    N = int(next(iterator))
    p = int(next(iterator))
    
    A = []
    for _ in range(N):
        row = []
        for _ in range(N):
            row.append(int(next(iterator)))
        A.append(row)
    
    # Identify positions of zeros
    zero_positions = []
    for i in range(N):
        for j in range(N):
            if A[i][j] == 0:
                zero_positions.append((i, j))
    
    K = len(zero_positions)
    
    if K == 0:
        # No zeros, just compute A^p mod p
        result = matrix_pow_mod(A, p, p)
        for i in range(N):
            print(*(result[i]))
        return
    
    # We need to compute sum over all (p-1)^K matrices B of B^p mod p
    # 
    # Key insight:
    # For a path of length p: i -> v1 -> v2 -> ... -> v_{p-1} -> j
    # The contribution to (B^p)[i,j] is product of edges along the path.
    # 
    # Sum over all B: for each path, we sum over all choices of zero edges.
    # For a zero edge, sum of choices is sum_{x=1}^{p-1} x = p-1 = -1 mod p.
    # 
    # So for a path with z zero edges, the sum is (product of fixed edges) * (-1)^z mod p.
    # 
    # Define M[u][v] = A[u][v] if A[u][v] != 0, else -1 mod p.
    # Then product of M[u][v] for all edges in the path = (product of fixed edges) * (-1)^z.
    # 
    # So the answer is (M^p)[i,j] mod p!
    
    # Build matrix M
    M = [[0] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            if A[i][j] != 0:
                M[i][j] = A[i][j] % p
            else:
                M[i][j] = (-1) % p
    
    # Compute M^p mod p
    result = matrix_pow_mod(M, p, p)
    
    for i in range(N):
        print(*(result[i]))

def matrix_mul_mod(A, B, mod):
    n = len(A)
    m = len(B[0])
    k = len(B)
    C = [[0] * m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            s = 0
            for l in range(k):
                s = (s + A[i][l] * B[l][j]) % mod
            C[i][j] = s
    return C

def matrix_pow_mod(A, p, mod):
    n = len(A)
    # Identity matrix
    result = [[0] * n for _ in range(n)]
    for i in range(n):
        result[i][i] = 1
    
    base = A
    exp = p
    
    while exp > 0:
        if exp % 2 == 1:
            result = matrix_mul_mod(result, base, mod)
        base = matrix_mul_mod(base, base, mod)
        exp //= 2
    
    return result

if __name__ == "__main__":
    solve()
