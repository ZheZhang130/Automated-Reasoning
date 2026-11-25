import sys

def solve():
    n = int(sys.stdin.readline().strip())
    if n % 2 == 1:
        # Odd: one '=' in the middle
        left = (n - 1) // 2
        right = left
        result = '-' * left + '=' + '-' * right
    else:
        # Even: two '=' in the middle
        left = n // 2 - 1
        right = left
        result = '-' * left + '==' + '-' * right
    print(result)

if __name__ == "__main__":
    solve()
