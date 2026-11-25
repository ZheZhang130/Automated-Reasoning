import sys

def solve():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        n = int(line)
    except ValueError:
        return

    if n % 2 == 1:
        # Odd length: must have exactly one '=' in the center
        # Fill rest with '-'
        half = (n - 1) // 2
        result = '-' * half + '=' + '-' * half
    else:
        # Even length: must have exactly two '=' adjacent in the center
        # Fill rest with '-'
        half = n // 2
        result = '-' * (half - 1) + '==' + '-' * (half - 1)
    
    print(result)

if __name__ == "__main__":
    solve()
