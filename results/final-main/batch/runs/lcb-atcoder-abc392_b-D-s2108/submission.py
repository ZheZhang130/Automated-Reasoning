import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    N = int(next(iterator))
    M = int(next(iterator))
    
    present = set()
    for _ in range(M):
        present.add(int(next(iterator)))
    
    missing = []
    for i in range(1, N + 1):
        if i not in present:
            missing.append(i)
    
    print(len(missing))
    print(" ".join(map(str, missing)))

if __name__ == "__main__":
    solve()
