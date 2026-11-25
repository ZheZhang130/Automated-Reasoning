import sys

def solve():
    try:
        input_data = sys.stdin.read().strip()
        if not input_data:
            return
        n = int(input_data)
        
        if n % 2 == 1:
            # Odd: one '=' in the middle
            half = (n - 1) // 2
            result = '-' * half + '=' + '-' * half
        else:
            # Even: two adjacent '=' in the middle
            half = n // 2 - 1
            result = '-' * half + '==' + '-' * half
        
        print(result)
    except Exception:
        pass

if __name__ == "__main__":
    solve()
