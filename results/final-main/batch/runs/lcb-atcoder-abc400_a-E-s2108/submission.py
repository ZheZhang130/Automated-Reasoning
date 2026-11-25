import sys

def solve():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        A = int(line)
        # We need A * B = 400, so B = 400 / A
        # B must be a positive integer, so A must divide 400
        if 400 % A == 0:
            print(400 // A)
        else:
            print(-1)
    except ValueError:
        pass

if __name__ == "__main__":
    solve()
