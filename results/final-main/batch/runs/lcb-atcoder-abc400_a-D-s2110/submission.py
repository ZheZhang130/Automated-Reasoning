import sys

def solve():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        a = int(line)
        if 400 % a == 0:
            print(400 // a)
        else:
            print(-1)
    except ValueError:
        pass

if __name__ == "__main__":
    solve()
