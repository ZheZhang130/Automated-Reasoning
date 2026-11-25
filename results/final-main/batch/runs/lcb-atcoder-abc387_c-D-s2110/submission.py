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
    for d in range(1, length):
        # For a fixed first digit f, other digits can be 0 to f-1
        # Number of positions = d - 1
        for f in range(1, 10):
            count = f ** (d - 1)
            total += count
    
    # Count snake numbers with same length as n
    # First digit must be <= first_digit of n
    for f in range(1, first_digit + 1):
        if f < first_digit:
            # First digit is f, remaining d-1 digits can be 0 to f-1
            count = f ** (length - 1)
            total += count
        else:
            # First digit equals first_digit of n
            # Check each subsequent digit
            valid = True
            for i in range(1, length):
                d = int(s[i])
                if d >= f:
                    valid = False
                    break
            if valid:
                total += 1
    
    return total

def main():
    line = sys.stdin.read().strip()
    L, R = map(int, line.split())
    ans = count_snake(R) - count_snake(L - 1)
    print(ans)

if __name__ == "__main__":
    main()
