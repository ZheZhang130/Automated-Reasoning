import sys

def mat_mul(A, B, p):
    n = len(A)
    C = [[0]*n for _ in range(n)]
    for i in range(n):
        for k in range(n):
            if A[i][k] == 0:
                continue
            aik = A[i][k]
            for j in range(n):
                C[i][j] = (C[i][j] + aik * B[k][j]) % p
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
    data = sys.stdin.read().split()
    it = iter(data)
    N = int(next(it))
    p = int(next(it))
    A = [[int(next(it)) for _ in range(N)] for _ in range(N)]
    K = sum(row.count(0) for row in A)
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
    A_pos = [row[:] for row in A]
    for i in range(N):
        for j in range(N):
            if A[i][j] == 0:
                A_pos[i][j] = 1
    A_pos = mat_pow(A_pos, p)
    ans = [row[:] for row in A_pos]
    for i in range(N):
        for j in range(N):
            if A[i][i] == 0:
                ans[i][j] = (ans[i][j] + A[i][j]) % p
            if A[j][j] == 0:
                ans[i][j] = (ans[i][j] + A[i][j]) % p
            if p == 3 and i != j and A[i][j] == 0:
                if A[j][i] != 0:
                    ans[i][j] = (ans[i][j] + A[j][i]) % p
    sign = -1 if K % 2 else 1
    for i in range(N):
        for j in range(N):
            ans[i][j] = (ans[i][j] + sign) % p
    for row in ans:
        print(*(x % p for x in row))

if __name__ == "__main__":
    solve()
