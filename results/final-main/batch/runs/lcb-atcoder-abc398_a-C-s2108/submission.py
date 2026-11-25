import sys

def solve():
    n = int(sys.stdin.readline().strip())
    if n % 2 == 1:
        # Odd: one '=' in the middle
        half = (n - 1) // 2
        print('-' * half + '=' + '-' * half)
    else:
        # Even: two adjacent '=' in the middle
        half = n // 2 - 1
        print('-' * half + '==' + '-' * half)

if __name__ == "__main__":
    solve()
