import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    M = int(input_data[1])
    A = set(int(x) for x in input_data[2:])
    
    missing = [x for x in range(1, N + 1) if x not in A]
    C = len(missing)
    
    print(C)
    print(" ".join(map(str, missing)))

if __name__ == "__main__":
    solve()
