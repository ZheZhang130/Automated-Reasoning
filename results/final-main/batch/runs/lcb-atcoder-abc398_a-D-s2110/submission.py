import sys

def solve():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        n = int(line)
        
        # For a palindrome of length N with exactly one or two '=':
        # - If N is odd, the single '=' must be at the center (index N//2)
        # - If N is even, the two '=' must be adjacent at the center (indices N//2 - 1 and N//2)
        
        if n % 2 == 1:
            # Odd length: one '=' at center
            result = ['-'] * n
            result[n // 2] = '='
        else:
            # Even length: two '=' at center
            result = ['-'] * n
            mid = n // 2
            result[mid - 1] = '='
            result[mid] = '='
        
        print(''.join(result))
    except Exception:
        pass

if __name__ == "__main__":
    solve()
