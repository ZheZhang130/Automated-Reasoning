import sys

def solve():
    n = int(sys.stdin.readline().strip())
    if n % 2 == 1:
        # Odd length: exactly one '=' in the center
        half = (n - 1) // 2
        print('-' * half + '=' + '-' * half)
    else:
        # Even length: exactly two adjacent '=' in the center
        half = n // 2
        print('-' * (half - 1) + '==' + '-' * (half - 1))

if __name__ == "__main__":
    solve()
