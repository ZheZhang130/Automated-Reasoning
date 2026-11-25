import sys

def count_snake(n):
    """Count snake numbers in [1, n] inclusive."""
    if n < 10:
        return 0
    
    s = str(n)
    L = len(s)
    first_digit = int(s[0])
    
    # Count numbers with fewer digits than n
    ans = 0
    for length in range(2, L):
        for d in range(1, 10):
            ans += d ** (length - 1)
    
    # Count numbers with same number of digits as n
    # For first digit < first_digit of n:
    for d in range(1, first_digit):
        ans += d ** (L - 1)
    
    # Now consider first digit = first_digit of n
    current_first = first_digit
    for i in range(1, L):
        limit = int(s[i])
        max_digit = min(limit - 1, current_first - 1)
        if max_digit >= 0:
            count = max_digit + 1
            remaining = L - 1 - i
            ans += count * (current_first) ** remaining
        if limit < current_first:
            break
    
    # Check if n itself is a snake number
    is_snake = True
    for i in range(1, L):
        if int(s[i]) >= current_first:
            is_snake = False
            break
    if is_snake:
        ans += 1
    
    return ans

def solve():
    line = sys.stdin.read().strip()
    L, R = map(int, line.split())
    ans = count_snake(R) - count_snake(L - 1)
    print(ans)

if __name__ == "__main__":
    solve()
