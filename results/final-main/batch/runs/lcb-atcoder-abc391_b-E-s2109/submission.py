import sys

def solve():
    input_data = sys.stdin.read().split()
    idx = 0
    N = int(input_data[idx])
    idx += 1
    M = int(input_data[idx])
    idx += 1
    
    S = []
    for _ in range(N):
        S.append(input_data[idx])
        idx += 1
    
    T = []
    for _ in range(M):
        T.append(input_data[idx])
        idx += 1
    
    # Find T in S
    # T is M x M, S is N x N
    # We need to find top-left (a, b) such that S[a+i-1][b+j-1] == T[i-1][j-1] for all i,j
    
    for a in range(1, N - M + 2):  # 1-indexed row start
        for b in range(1, N - M + 2):  # 1-indexed col start
            match = True
            for i in range(M):
                for j in range(M):
                    if S[a + i - 1][b + j - 1] != T[i][j]:
                        match = False
                        break
                if not match:
                    break
            if match:
                print(f"{a} {b}")
                return

if __name__ == "__main__":
    solve()
