import sys

def solve():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        n = int(line)
        if n % 2 == 1:
            # Odd: one '=' in the middle
            half = n // 2
            result = '-' * half + '=' + '-' * half
        else:
            # Even: two adjacent '=' in the middle
            half = n // 2
            result = '-' * (half - 1) + '==' + '-' * (half - 1)
        print(result)
    except Exception:
        pass

if __name__ == "__main__":
    solve()
