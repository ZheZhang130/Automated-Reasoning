import sys

def solve():
    n = int(sys.stdin.readline().strip())
    if n % 2 == 0:
        # Even length: use two adjacent '=' in the center
        half = (n - 2) // 2
        print('-' * half + '==' + '-' * half)
    else:
        # Odd length: use one '=' in the center
        half = n // 2
        print('-' * half + '=' + '-' * half)

if __name__ == "__main__":
    solve()
