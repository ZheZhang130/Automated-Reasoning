import sys

def count_snake(n):
    """Count snake numbers in [1, n]"""
    if n < 10:
        return 0
    
    s = str(n)
    length = len(s)
    total = 0
    
    # Count snake numbers with fewer digits than n
    for d in range(2, length):
        # First digit can be 1..9
        # Remaining d-1 digits can be 0..(first_digit-1)
        first_digit = 9
        for f in range(1, first_digit + 1):
            # Each of the remaining d-1 positions has f choices (0 to f-1)
            total += f ** (d - 1)
    
    # Count snake numbers with same number of digits as n
    # We need to count numbers of length 'length' where first digit > all others
    # and the number is <= n
    
    # First digit must be at least 1 and at most int(s[0])
    # But if first digit < int(s[0]), then remaining digits can be anything from 0 to first_digit-1
    # If first digit == int(s[0]), we need to check the remaining digits against n's suffix
    
    first_digit_limit = int(s[0])
    
    # Case 1: first digit < first_digit_limit
    for f in range(1, first_digit_limit):
        total += f ** (length - 1)
    
    # Case 2: first digit == first_digit_limit
    # Now we need to count valid suffixes of length (length-1) where each digit < first_digit_limit
    # and the number formed is <= n[1:]
    
    suffix_limit = s[1:]
    if suffix_limit:
        # We need to count numbers of length (length-1) with digits in [0, first_digit_limit-1]
        # that are <= suffix_limit
        # This is a digit DP or careful counting
        
        # Let's iterate through each position
        limit_val = first_digit_limit
        for i in range(length - 1):
            digit_limit = limit_val - 1
            # At position i, we can put any digit from 0 to digit_limit
            # But we need to be careful about the limit
            
            # Actually, let's think differently:
            # We want to count numbers d1 d2 ... d_{k-1} where d1 = first_digit_limit
            # and d2, ..., d_{k-1} are all < d1
            # and the number is <= n
            
            # Let's build the count digit by digit
            pass
        
        # Simpler approach: iterate through all possible suffixes
        # But that's too slow for large numbers
        
        # Better: use digit DP logic
        # We want to count sequences d2, d3, ..., d_{k-1} where:
        # 1. Each di < first_digit_limit
        # 2. The number d2d3...d_{k-1} <= suffix_limit
        
        # Let's count by iterating through positions
        # At each position, we can choose a digit from 0 to min(digit_limit, current_limit_digit)
        # If we choose strictly less than current_limit_digit, then remaining positions can be anything (0 to digit_limit)
        # If we choose equal, we continue to next position
        
        k = length - 1
        current_limit = suffix_limit
        digit_limit = first_digit_limit - 1
        
        # Count valid suffixes
        count_suffix = 0
        for i in range(k):
            if i == k - 1:
                # Last digit: can be from 0 to min(digit_limit, int(current_limit[i]))
                # But we need to be <= current_limit[i]
                # Actually, at the last position, we can have any digit from 0 to min(digit_limit, int(current_limit[i]))
                # Wait, we need to count numbers <= current_limit
                # At position i, if we pick a digit < current_limit[i], then remaining positions can be anything
                # If we pick == current_limit[i], we continue
                
                # This is getting complicated. Let me use a different approach.
                pass
            
            # Let's use a simpler digit-by-digit counting
            # At position i (0-indexed from left of suffix), we have current_limit_digit = int(current_limit[i])
            # We can choose digits from 0 to digit_limit
            # If digit_limit < current_limit_digit, then we can choose 0 to digit_limit, and for each choice,
            # the remaining positions can be anything (0 to digit_limit)
            # If digit_limit >= current_limit_digit, then we can choose 0 to current_limit_digit-1, and for each,
            # remaining positions can be anything (0 to digit_limit)
            # And if we choose current_limit_digit, we continue to next position
            
            current_digit = int(current_limit[i])
            if digit_limit < current_digit:
                # We can choose 0 to digit_limit, and for each choice, remaining (k-1-i) positions can be 0 to digit_limit
                count_suffix += (digit_limit + 1) ** (k - 1 - i) * (digit_limit + 1)
                # Wait, that's not right. Let me reconsider.
                # At position i, we choose a digit d from 0 to digit_limit
                # If d < current_digit, then remaining positions can be anything from 0 to digit_limit
                # Number of such d is min(digit_limit + 1, current_digit)
                # For each such d, remaining (k-1-i) positions have (digit_limit + 1) choices each
                # So we add min(digit_limit + 1, current_digit) * (digit_limit + 1) ** (k - 1 - i)
                # But wait, we also need to handle the case where we continue with d == current_digit
                
                # Actually, let me restart this logic
                pass
            else:
                # digit_limit >= current_digit
                # We can choose 0 to current_digit-1, and for each, remaining positions can be 0 to digit_limit
                count_suffix += current_digit * (digit_limit + 1) ** (k - 1 - i)
                # And we continue with d == current_digit
        
        # Hmm, this is getting messy. Let me use a cleaner approach.
        pass
    
    # Let me rewrite this more carefully
    total = 0
    
    # Count snake numbers with fewer digits
    for d in range(2, length):
        for f in range(1, 10):
            total += f ** (d - 1)
    
    # Count snake numbers with same number of digits
    first_digit_limit = int(s[0])
    
    # First digit < first_digit_limit
    for f in range(1, first_digit_limit):
        total += f ** (length - 1)
    
    # First digit == first_digit_limit
    # Now count valid suffixes
    suffix = s[1:]
    k = length - 1
    
    # We need to count sequences d2, d3, ..., d_k where each di < first_digit_limit
    # and the number d2d3...d_k <= suffix
    
    # Use digit DP
    # State: (position, is_less)
    # But we can do it iteratively
    
    for i in range(k):
        current_digit = int(suffix[i])
        # We can choose digits from 0 to first_digit_limit - 1
        # If we choose a digit < current_digit, then remaining positions can be anything from 0 to first_digit_limit - 1
        # If we choose a digit == current_digit, we continue to next position
        # If current_digit >= first_digit_limit, then we can choose 0 to first_digit_limit - 1 for all remaining
        
        if current_digit >= first_digit_limit:
            # All digits from 0 to first_digit_limit - 1 are valid and less than current_digit
            # So for this position, we can choose any of 0 to first_digit_limit - 1
            # And for each choice, remaining positions can be anything
            # But we're at position i, so there are (k - 1 - i) positions after this
            # Actually, we need to count all valid completions
            
            # If we choose d < current_digit (which is all d from 0 to first_digit_limit - 1 since current_digit >= first_digit_limit)
            # Then remaining (k - 1 - i) positions can be anything from 0 to first_digit_limit - 1
            # Number of choices for this position: first_digit_limit
            # Number of completions: first_digit_limit ** (k - 1 - i)
            # Total for this position: first_digit_limit * first_digit_limit ** (k - 1 - i) = first_digit_limit ** (k - i)
            # But wait, we also need to consider that we might continue to the next position
            
            # Actually, let me think again.
            # At position i, we can choose d from 0 to first_digit_limit - 1
            # If d < current_digit, then we're strictly less, and remaining positions can be anything
            # If d == current_digit, we continue
            # If d > current_digit, not allowed (but d <= first_digit_limit - 1 and current_digit >= first_digit_limit, so d < current_digit always)
            
            # So all choices d from 0 to first_digit_limit - 1 are < current_digit
            # For each such d, remaining (k - 1 - i) positions can be 0 to first_digit_limit - 1
            # So we add first_digit_limit * (first_digit_limit ** (k - 1 - i)) = first_digit_limit ** (k - i)
            # But we also need to handle the case where we continue with d == current_digit, but current_digit >= first_digit_limit, so d == current_digit is not allowed
            
            # So we just add first_digit_limit ** (k - i) and we're done with this branch
            total += first_digit_limit ** (k - i)
            break  # We've counted all valid completions
        else:
            # current_digit < first_digit_limit
            # We can choose d from 0 to current_digit - 1, and for each, remaining positions can be 0 to first_digit_limit - 1
            # Number of such d: current_digit
            # For each, completions: first_digit_limit ** (k - 1 - i)
            total += current_digit * (first_digit_limit ** (k - 1 - i))
            # And we continue with d == current_digit to the next position
    
    # After the loop, if we haven't broken, we need to check if the suffix itself is valid
    # The suffix is valid if all its digits are < first_digit_limit
    # We've been counting strictly less, so we need to check if the suffix itself is valid
    # Actually, the loop above counts all strictly less cases. We need to check if the suffix itself is valid.
    
    # Check if suffix is valid (all digits < first_digit_limit)
    valid_suffix = True
    for c in suffix:
        if int(c) >= first_digit_limit:
            valid_suffix = False
            break
    
    if valid_suffix:
        total += 1
    
    return total

def solve():
    line = sys.stdin.readline().strip()
    L, R = map(int, line.split())
    ans = count_snake(R) - count_snake(L - 1)
    print(ans)

if __name__ == "__main__":
    solve()
