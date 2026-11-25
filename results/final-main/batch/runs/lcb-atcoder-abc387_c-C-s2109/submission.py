import sys

def count_snake_upto(x: int) -> int:
    """Count Snake numbers in [10, x] inclusive."""
    if x < 10:
        return 0
    
    s = str(x)
    n = len(s)
    leading_digit = int(s[0])
    
    total = 0
    
    # 1. Count all Snake numbers with fewer digits than x
    # For length k (2 to n-1), leading digit d can be 1..9.
    # For each d, there are d^(k-1) valid numbers.
    for k in range(2, n):
        for d in range(1, 10):
            total += d ** (k - 1)
    
    # 2. Count Snake numbers with same length n and leading digit < leading_digit of x
    for d in range(1, leading_digit):
        total += d ** (n - 1)
    
    # 3. Count Snake numbers with same length n and leading digit == leading_digit of x
    # We need to check if x itself is a Snake number and count those strictly less than x
    # that share the same prefix.
    # Actually, we count valid suffixes for the current leading digit that are <= the suffix of x.
    # But the rule is: every digit must be < leading_digit.
    # So for each position i from 1 to n-1, the digit s[i] must be < leading_digit.
    # If at any point s[i] >= leading_digit, then x is not a Snake number, and we stop.
    # However, we also need to count numbers that are strictly less than x but still Snake.
    # Those would be numbers that match x up to some position i, then have a digit < s[i]
    # (but still < leading_digit), and then any valid suffix.
    
    # Let's reframe:
    # We are counting Snake numbers of length n with leading digit = leading_digit.
    # Such a number is valid if for all i in 1..n-1, digit[i] < leading_digit.
    # We want to count those <= x.
    # Since the leading digit is fixed, we look at the suffix.
    # For each position i from 1 to n-1:
    #   Let current digit in x be d_curr = int(s[i]).
    #   The valid digits for this position are 0..min(leading_digit-1).
    #   If d_curr < leading_digit:
    #       Then any digit < d_curr at this position (and still < leading_digit) would make the number smaller.
    #       The number of choices for this position is d_curr.
    #       For the remaining positions (n-1-i), each can be any digit from 0..leading_digit-1.
    #       So we add d_curr * (leading_digit)^(n-1-i).
    #       Then we continue to the next position (since we are still matching x).
    #   If d_curr >= leading_digit:
    #       Then x itself is not a Snake number (since this digit violates the condition).
    #       Also, no number with the same prefix up to i-1 and then a digit < d_curr can be valid
    #       if that digit is >= leading_digit? Wait.
    #       Actually, if d_curr >= leading_digit, then any valid digit at this position must be < leading_digit.
    #       So the valid digits are 0..leading_digit-1.
    #       The count of valid digits strictly less than d_curr is leading_digit (since all 0..leading_digit-1 are < d_curr).
    #       So we add leading_digit * (leading_digit)^(n-1-i).
    #       Then we stop because we cannot match x anymore (x is invalid here).
    
    # Wait, let's re-evaluate the condition for stopping.
    # We are counting numbers y such that:
    #   y has length n
    #   y[0] == leading_digit
    #   for all j, y[j] < y[0]
    #   y <= x
    
    # We iterate i from 1 to n-1.
    # At position i, let d_curr = x[i].
    # The valid digits for y[i] are 0..min(leading_digit-1).
    # Let max_valid = min(leading_digit-1).
    # The number of choices for y[i] that are < d_curr is min(d_curr, max_valid + 1).
    # Actually, the valid digits are 0..max_valid.
    # The count of valid digits < d_curr is min(d_curr, max_valid + 1).
    # But wait, if d_curr > max_valid, then all valid digits (0..max_valid) are < d_curr.
    # So the count is max_valid + 1 = leading_digit.
    # If d_curr <= max_valid, then the count is d_curr.
    # So in both cases, the count is min(d_curr, leading_digit).
    # However, we must also ensure that we don't count numbers that are invalid because of previous digits.
    # But we are building the count by branching at the first position where y differs from x.
    # So if we are at position i, it means y[0..i-1] == x[0..i-1].
    # Since x[0] is the leading digit, and for j < i, x[j] must have been < x[0] for x to be potentially valid?
    # No, we are counting y <= x.
    # If at some position j < i, x[j] >= leading_digit, then x is not a Snake number.
    # But we are counting y that are Snake numbers.
    # If x[j] >= leading_digit, then any y that matches x up to j-1 must have y[j] < leading_digit.
    # So y[j] < x[j] automatically.
    # So we can still count.
    # But if x[j] < leading_digit, then we have two cases:
    #   y[j] < x[j]: then y < x. We count these.
    #   y[j] == x[j]: then we continue to next position.
    #   y[j] > x[j]: not possible since we want y <= x.
    # So the logic is:
    #   For each position i from 1 to n-1:
    #     d_curr = int(s[i])
    #     max_valid = leading_digit - 1
    #     count_valid_less = min(d_curr, max_valid + 1)
    #     total += count_valid_less * (leading_digit) ** (n - 1 - i)
    #     if d_curr > max_valid:
    #         # x[i] is invalid for a Snake number.
    #         # So x itself is not a Snake number.
    #         # And we cannot match x anymore because any valid digit is < d_curr.
    #         # So we stop.
    #         break
    #     else:
    #         # d_curr <= max_valid.
    #         # We add the count for y[i] < d_curr.
    #         # Then we consider y[i] == d_curr and continue.
    #         # But wait, if d_curr <= max_valid, then d_curr is a valid digit.
    #         # So we can match x at this position and continue.
    #         # However, we also need to check if x itself is a Snake number at the end.
    #         # If we finish the loop without breaking, then x is a Snake number.
    #         # So we add 1 at the end.
    #         pass
    
    # Let's trace:
    #   For each i from 1 to n-1:
    #     d_curr = int(s[i])
    #     max_valid = leading_digit - 1
    #     count_valid_less = min(d_curr, max_valid + 1)
    #     total += count_valid_less * (leading_digit) ** (n - 1 - i)
    #     if d_curr > max_valid:
    #         break
    #   else:
    #       # If we didn't break, then x is a valid Snake number.
    #       total += 1
    
    # This logic seems correct.
    
    for i in range(1, n):
        d_curr = int(s[i])
        max_valid = leading_digit - 1
        count_valid_less = min(d_curr, max_valid + 1)
        total += count_valid_less * (leading_digit ** (n - 1 - i))
        if d_curr > max_valid:
            break
    else:
        total += 1
    
    return total

def main():
    data = sys.stdin.read().split()
    if not data:
        return
    L = int(data[0])
    R = int(data[1])
    ans = count_snake_upto(R) - count_snake_upto(L - 1)
    print(ans)

if __name__ == "__main__":
    main()
