import sys

def count_snake(n):
    """Count snake numbers in [1, n] inclusive."""
    if n < 10:
        return 0
    s = str(n)
    m = len(s)
    total = 0
    
    # Count snake numbers with fewer digits than n
    for d in range(1, m):
        # First digit can be 1..9
        # Remaining d-1 digits can be 0..(first_digit-1)
        first_digit = 9
        for fd in range(1, first_digit + 1):
            # Each of the remaining d-1 positions has fd choices (0 to fd-1)
            total += fd ** (d - 1)
    
    # Count snake numbers with same number of digits as n
    # We need to count numbers with same length as n where first digit > all others
    # and the number <= n
    
    # First digit must be <= first digit of n
    fd_n = int(s[0])
    
    # Case 1: First digit < fd_n
    # Then remaining digits can be anything from 0 to (first_digit - 1)
    for fd in range(1, fd_n):
        total += fd ** (m - 1)
    
    # Case 2: First digit == fd_n
    # Then we need to count valid suffixes <= s[1:]
    # where each digit in suffix is < fd_n
    # We iterate through positions and count valid combinations
    
    # For the remaining m-1 digits, each can be 0..(fd_n-1)
    # But we need the number formed to be <= s[1:]
    
    # Let's build digit by digit
    limit = s[1:]
    for i in range(m - 1):
        d_limit = int(limit[i])
        # Digits 0 to d_limit-1 are strictly less, so any combination works
        # Digits d_limit to fd_n-1 are equal or greater, need to check further
        
        # Count combinations where digit at position i is < d_limit
        for d in range(d_limit):
            # Remaining positions can be 0..(fd_n-1)
            remaining = (m - 1) - (i + 1)
            total += d * (fd_n) ** remaining
        
        # If d_limit >= fd_n, then we can use d_limit as well (but must be < fd_n)
        # Actually, we need digit < fd_n, so valid digits are 0..min(d_limit, fd_n-1)
        # But we already counted 0..d_limit-1 above
        # If d_limit < fd_n, we need to continue with the same prefix
        # If d_limit >= fd_n, then we can use up to fd_n-1, but we need to check if
        # the number with digit = d_limit is <= limit
        
        # Actually, let's reconsider. We need to count numbers where:
        # - First digit = fd_n
        # - All other digits < fd_n
        # - Number <= n
        
        # At position i, we can put any digit d where 0 <= d < fd_n
        # If d < d_limit, then any suffix works
        # If d == d_limit, we continue to next position
        # If d > d_limit, then this number is > n, so we stop
        
        # But we also have the constraint that d < fd_n
        
        # So valid digits at position i are 0..min(d_limit, fd_n-1)
        # For d < d_limit: count = (fd_n) ** remaining
        # For d == d_limit: continue if d_limit < fd_n
        
        # Let's simplify: count all combinations with first digit = fd_n
        # and all other digits < fd_n, then subtract those > n
        
        # Actually, let's use a different approach for the same-length case
        
    # Simpler approach for same length:
    # Count all numbers with first digit = fd_n and all other digits < fd_n
    # Then subtract those > n
    
    # Total with first digit = fd_n and all others < fd_n:
    total_same_fd = (fd_n) ** (m - 1)
    
    # Now subtract those > n
    # A number is > n if at some position i, digit > s[i]
    # But we also need digit < fd_n
    
    # Let's count directly by iterating through positions
    # For each position, count valid digits that make the number <= n
    
    # Reset and do it properly
    total = 0
    
    # Fewer digits
    for d in range(1, m):
        for fd in range(1, 10):
            total += fd ** (d - 1)
    
    # Same digits
    # First digit from 1 to fd_n-1
    for fd in range(1, fd_n):
        total += fd ** (m - 1)
    
    # First digit = fd_n
    # Now count valid suffixes
    # We need to count numbers where each digit < fd_n and number <= n
    
    # Build digit by digit
    for i in range(m - 1):
        d_limit = int(limit[i])
        # Valid digits at this position: 0 to min(d_limit, fd_n-1)
        # But we need to handle the case where we match the limit
        
        # Count digits strictly less than d_limit
        for d in range(min(d_limit, fd_n)):
            remaining = (m - 1) - (i + 1)
            total += (fd_n) ** remaining
        
        # If d_limit < fd_n, we can continue with d = d_limit
        # If d_limit >= fd_n, we can use up to fd_n-1, but we already counted those
        # Actually, if d_limit >= fd_n, then all digits 0..fd_n-1 are < d_limit
        # So we've already counted all valid digits
        
        # If d_limit < fd_n, we need to continue with d = d_limit
        if d_limit < fd_n:
            # Continue to next position with same prefix
            pass
        else:
            # d_limit >= fd_n, so we've counted all valid digits (0..fd_n-1)
            # and the number with prefix matching n up to this point is valid
            # Actually, we need to check if the full number with all digits = fd_n-1 is <= n
            # But since d_limit >= fd_n > fd_n-1, any digit < fd_n is < d_limit
            # So we've counted all valid combinations
            break
    
    return total

def solve():
    line = sys.stdin.readline().strip()
    L, R = map(int, line.split())
    ans = count_snake(R) - count_snake(L - 1)
    print(ans)

if __name__ == "__main__":
    solve()
