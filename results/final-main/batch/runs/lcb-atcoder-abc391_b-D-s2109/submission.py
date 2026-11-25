import sys

def solve():
    # Read N and M
    first_line = sys.stdin.readline().strip()
    if not first_line:
        return
    N, M = map(int, first_line.split())
    
    # Read grid S
    S = []
    for _ in range(N):
        S.append(sys.stdin.readline().strip())
    
    # Read grid T
    T = []
    for _ in range(M):
        T.append(sys.stdin.readline().strip())
    
    # Search for T in S
    # We need to find top-left (a, b) such that S[a+i-1][b+j-1] == T[i-1][j-1] for all i,j
    # Since 1-based indexing in output, we'll use 0-based internally and convert at the end
    
    for a in range(N - M + 1):
        for b in range(N - M + 1):
            match = True
            for i in range(M):
                for j in range(M):
                    if S[a + i][b + j] != T[i][j]:
                        match = False
                        break
                if not match:
                    break
            if match:
                print(f"{a + 1} {b + 1}")
                return

if __name__ == "__main__":
    solve()
