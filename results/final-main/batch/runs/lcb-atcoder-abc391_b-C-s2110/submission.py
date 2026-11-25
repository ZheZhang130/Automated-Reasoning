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
    
    # Search for T in S
    for a in range(1, N - M + 2):  # 1-based row index
        for b in range(1, N - M + 2):  # 1-based column index
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
