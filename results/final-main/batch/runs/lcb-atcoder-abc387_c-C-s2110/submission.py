import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    L = int(input_data[0])
    R = int(input_data[1])

    # Precompute powers of digits 1-9
    pow_base = [[0] * 20 for _ in range(10)]
    for d in range(1, 10):
        p = 1
        for e in range(20):
            pow_base[d][e] = p
            p *= d

    def count_snake_at_most(X):
        if X < 10:
            return 0
        s = str(X)
        n = len(s)
        total = 0
        
        # Count all snake numbers with fewer digits than X
        for length in range(2, n):
            exp = length - 1
            for d in range(1, 10):
                total += pow_base[d][exp]
        
        # Count snake numbers with same number of digits as X
        first_digit = int(s[0])
        limit = first_digit
        
        # Leading digit d can be from 1 to first_digit - 1
        for d in range(1, first_digit):
            total += pow_base[d][n - 1]
        
        # Now consider leading digit == first_digit
        # We need to count valid suffixes that are <= X's suffix
        for i in range(1, n):
            digit = int(s[i])
            remaining = n - 1 - i
            if digit < limit:
                total += digit * pow_base[limit][remaining]
            elif digit == limit:
                continue
            else:
                # digit > limit, so we can choose any digit from 0 to limit-1
                total += limit * pow_base[limit][remaining]
                break
        
        return total

    ans = count_snake_at_most(R) - count_snake_at_most(L - 1)
    print(ans)

if __name__ == "__main__":
    solve()
