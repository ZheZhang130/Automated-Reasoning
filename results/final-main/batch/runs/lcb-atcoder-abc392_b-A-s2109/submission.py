import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    
    N = int(data[0])
    M = int(data[1])
    A = set(int(x) for x in data[2:2+M])
    
    missing = []
    for i in range(1, N + 1):
        if i not in A:
            missing.append(i)
    
    print(len(missing))
    print(" ".join(map(str, missing)))

if __name__ == "__main__":
    solve()
