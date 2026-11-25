import sys

def count_snake_upto(n):
    """Count Snake numbers in [10, n] inclusive."""
    if n < 10:
        return 0
    
    s = str(n)
    length = len(s)
    leading_digit = int(s[0])
    
    total = 0
    
    # 1. Count all Snake numbers with fewer digits than n
    for k in range(2, length):
        for d in range(1, 10):
            total += d ** (k - 1)
    
    # 2. Count Snake numbers with same length as n
    # Case 2a: Leading digit d < leading_digit of n
    for d in range(1, leading_digit):
        total += d ** (length - 1)
    
    # Case 2b: Leading digit equals leading_digit of n
    # We need to count numbers with leading digit = leading_digit that are < n
    for i in range(1, length):
        digit_at_i = int(s[i])
        limit = min(digit_at_i - 1, leading_digit - 1)
        if limit >= 0:
            remaining_len = length - 1 - i
            total += (limit + 1) * (leading_digit ** remaining_len)
        else:
            break
    
    # 3. Check if n itself is a Snake number
    is_snake = True
    for j in range(1, length):
        if int(s[j]) >= leading_digit:
            is_snake = False
            break
    if is_snake:
        total += 1
    
    return total

def main():
    line = sys.stdin.readline().strip()
    if not line:
        return
    L, R = map(int, line.split())
    ans = count_snake_upto(R) - count_snake_upto(L - 1)
    print(ans)

if __name__ == "__main__":
    main()
