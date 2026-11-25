import sys

def count_snake(n):
    """Count snake numbers in [1, n] inclusive."""
    if n < 10:
        return 0
    
    s = str(n)
    length = len(s)
    first_digit = int(s[0])
    
    # Count snake numbers with fewer digits than n
    total = 0
    for d_len in range(2, length):
        # First digit can be from 1 to 9
        for first in range(1, 10):
            # For a fixed first digit, each of the remaining (d_len-1) digits
            # can be any digit from 0 to first-1
            total += first ** (d_len - 1)
    
    # Count snake numbers with the same number of digits as n
    for first in range(1, first_digit + 1):
        if first == first_digit:
            # First digit matches n's first digit
            # Count numbers of length 'length' starting with 'first'
            # where all other digits are < first, and the number <= n
            
            suffix_str = s[1:]
            suffix_len = length - 1
            
            # Count numbers of length suffix_len with digits in 0..first-1 that are <= suffix_str
            count_for_first = 0
            tight = True
            
            for i in range(suffix_len):
                digit_limit = first - 1  # max digit allowed
                
                if tight:
                    upper = min(digit_limit, int(suffix_str[i]))
                else:
                    upper = digit_limit
                
                # Count digits strictly less than upper
                for d in range(0, upper):
                    remaining_positions = suffix_len - 1 - i
                    count_for_first += digit_limit ** remaining_positions
                
                # Check if we can continue with digit == n[i]
                if tight and int(suffix_str[i]) <= digit_limit:
                    # Continue to next position
                    pass
                else:
                    tight = False
            
            # After the loop, if we're still tight, check if n itself is valid
            if tight:
                is_valid = True
                for i in range(1, length):
                    if int(s[i]) >= first:
                        is_valid = False
                        break
                if is_valid:
                    count_for_first += 1
            
            total += count_for_first
        else:
            # First digit is less than n's first digit
            # Then all remaining digits can be any digit in 0..first-1
            total += first ** (length - 1)
    
    return total

def solve():
    line = sys.stdin.read().strip()
    L, R = map(int, line.split())
    ans = count_snake(R) - count_snake(L - 1)
    print(ans)

if __name__ == "__main__":
    solve()
