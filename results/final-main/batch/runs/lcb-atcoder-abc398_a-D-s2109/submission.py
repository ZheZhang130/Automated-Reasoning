import sys

def solve():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        n = int(line)
        
        # For odd N: place one '=' at the middle
        # For even N: place two adjacent '=' at the middle
        
        if n % 2 == 1:
            # Odd: middle index is n//2
            mid = n // 2
            s = ['-'] * n
            s[mid] = '='
        else:
            # Even: middle two indices are n//2 - 1 and n//2
            mid1 = n // 2 - 1
            mid2 = n // 2
            s = ['-'] * n
            s[mid1] = '='
            s[mid2] = '='
        
        print(''.join(s))
    except Exception:
        pass

if __name__ == "__main__":
    solve()
