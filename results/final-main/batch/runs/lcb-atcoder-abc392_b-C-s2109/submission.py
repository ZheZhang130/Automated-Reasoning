import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    N = int(next(iterator))
    M = int(next(iterator))
    
    present = [False] * (N + 1)
    
    for _ in range(M):
        val = int(next(iterator))
        present[val] = True
    
    missing = []
    for i in range(1, N + 1):
        if not present[i]:
            missing.append(i)
    
    print(len(missing))
    print(" ".join(map(str, missing)))

if __name__ == "__main__":
    solve()
