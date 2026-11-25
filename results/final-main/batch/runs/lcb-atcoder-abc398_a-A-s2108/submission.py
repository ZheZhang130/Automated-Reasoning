import sys

def solve():
    n = int(sys.stdin.readline().strip())
    if n % 2 == 0:
        # Even length: use one '=' at position n//2 - 1 (before the center)
        # This creates a palindrome with exactly one '='
        half = n // 2
        print('-' * (half - 1) + '=' + '-' * half)
    else:
        # Odd length: use two adjacent '=' in the center
        half = (n - 2) // 2
        print('-' * half + '==' + '-' * half)

if __name__ == "__main__":
    solve()
