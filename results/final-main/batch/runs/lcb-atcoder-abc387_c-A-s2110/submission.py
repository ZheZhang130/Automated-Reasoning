import sys

def count_snake(n):
    """Count snake numbers in [1, n] inclusive."""
    if n < 10:
        return 0
    
    s = str(n)
    L = len(s)
    first_digit = int(s[0])
    
    # Count numbers with fewer digits
    ans = 0
    for length in range(2, L):
        # For a fixed first digit d, remaining (length-1) digits can be 0..d
        # So there are (d+1) choices for each of the remaining positions
        for d in range(1, 10):
            ans += (d + 1) ** (length - 1)
    
    # Count numbers with same number of digits as n
    # First digit must be <= first_digit of n
    # For first digit d < first_digit: remaining digits can be 0..d
    for d in range(1, first_digit):
        ans += (d + 1) ** (L - 1)
    
    # For first digit = first_digit of n:
    # We need to count valid completions that are <= n
    # At each position i from 1 to L-1:
    #   We can put any digit d in [0, first_digit-1]
    #   If d < s[i], then all remaining positions can be 0..first_digit-1
    #   If d == s[i], we continue to next position
    #   If d > s[i], this is invalid
    
    for i in range(1, L):
        digit = int(s[i])
        # We can put digits 0..min(digit-1, first_digit-1) at this position
        # and then all remaining positions can be 0..first_digit-1
        upper = min(digit - 1, first_digit - 1)
        if upper >= 0:
            count = upper + 1
            remaining = L - 1 - i
            ans += count * (first_digit) ** remaining
    
    return ans

def solve():
    line = sys.stdin.read().strip()
    L, R = map(int, line.split())
    ans = count_snake(R) - count_snake(L - 1)
    print(ans)

if __name__ == "__main__":
    solve()
