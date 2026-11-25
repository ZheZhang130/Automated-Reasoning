import sys

def solve():
    try:
        input_data = sys.stdin.read().strip()
        if not input_data:
            return
        A = int(input_data)
        if 400 % A == 0:
            print(400 // A)
        else:
            print(-1)
    except Exception:
        pass

if __name__ == "__main__":
    solve()
