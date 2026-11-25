import sys

def mat_mul(A, B, p):
    n = len(A)
    C = [[0]*n for _ in range(n)]
    for i in range(n):
        for k in range(n):
            if A[i][k] == 0:
                continue
            for j in range(n):
                C[i][j] = (C[i][j] + A[i][k] * B[k][j]) % p
    return C

def mat_pow(A, p):
    n = len(A)
    res = [[0]*n for _ in range(n)]
    for i in range(n):
        res[i][i] = 1
    base = [row[:] for row in A]
    while p > 0:
        if p & 1:
            res = mat_mul(res, base, p)
        base = mat_mul(base, base, p)
        p >>= 1
    return res

def solve():
    input_data = sys.stdin.read().split()
    it = iter(input_data)
    N = int(next(it))
    p = int(next(it))
    A = []
    for _ in range(N):
        row = [int(next(it)) for _ in range(N)]
        A.append(row)

    if p == 2:
        B = [row[:] for row in A]
        for i in range(N):
            for j in range(N):
                if B[i][j] == 0:
                    B[i][j] = 1
        B = mat_mul(B, B, 2)
        for row in B:
            print(*(x % 2 for x in row))
        return

    K = 0
    for row in A:
        for x in row:
            if x == 0:
                K += 1

    A1 = [row[:] for row in A]
    for i in range(N):
        for j in range(N):
            if A[i][j] == 0:
                A1[i][j] = 1

    Ap = mat_pow(A1, p)

    correction = 0
    for i in range(N):
        for j in range(N):
            if i != j and A[i][j] == 0:
                correction = (correction + A[j][i]) % p

    sign = -1 if (K % 2 == 1) else 1

    ans = [[0]*N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            val = (Ap[i][j] + correction) % p
            ans[i][j] = (val * sign) % p

    for row in ans:
        print(*(x % p for x in row))

solve()
