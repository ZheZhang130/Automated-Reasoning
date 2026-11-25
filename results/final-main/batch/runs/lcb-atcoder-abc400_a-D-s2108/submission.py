import sys

def solve():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        A = int(line)
        if 400 % A == 0:
            print(400 // A)
        else:
            print(-1)
    except ValueError:
        pass

if __name__ == "__main__":
    solve()
