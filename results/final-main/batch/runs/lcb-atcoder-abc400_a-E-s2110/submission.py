import sys

def solve():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        A = int(line)
        total = 400
        # We need A * B = 400, so B = 400 / A
        # B must be a positive integer, so A must divide 400
        if total % A == 0:
            B = total // A
            print(B)
        else:
            print(-1)
    except ValueError:
        pass

if __name__ == "__main__":
    solve()
