import sys

def count_snake(n):
    """Count snake numbers in [1, n] inclusive."""
    if n < 10:
        return 0
    
    s = str(n)
    length = len(s)
    first_digit = int(s[0])
    
    # Count numbers with fewer digits than n
    total = 0
    for d_len in range(2, length):
        for d in range(1, 10):
            total += d ** (d_len - 1)
    
    # Now count numbers with the same number of digits as n, that are <= n
    digits = [int(c) for c in s]
    m = len(digits)
    
    for d in range(1, 10):
        if d < digits[0]:
            total += d ** (m - 1)
            continue
        
        if d > digits[0]:
            continue
        
        # d == digits[0]
        current_prefix_valid = True
        for i in range(1, m):
            limit = digits[i]
            max_digit = min(d - 1, limit - 1)
            if max_digit >= 0:
                count_choices = max_digit + 1
                total += count_choices * (d - 1) ** (m - 1 - i)
            
            if limit >= d:
                current_prefix_valid = False
                break
        
        if current_prefix_valid:
            total += 1
    
    return total

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    L = int(data[0])
    R = int(data[1])
    ans = count_snake(R) - count_snake(L - 1)
    print(ans)

if __name__ == "__main__":
    solve()
