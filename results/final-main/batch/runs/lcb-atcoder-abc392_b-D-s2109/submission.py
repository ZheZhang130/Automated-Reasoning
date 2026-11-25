import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0])
    m = int(data[1])
    a = set(int(x) for x in data[2:2+m])
    missing = [i for i in range(1, n + 1) if i not in a]
    print(len(missing))
    print(' '.join(map(str, missing)))

if __name__ == "__main__":
    solve()
