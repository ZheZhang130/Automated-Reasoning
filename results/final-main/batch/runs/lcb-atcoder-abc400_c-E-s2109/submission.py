import sys
import math

def count_good_integers(N):
    # We need to count numbers X <= N such that X = 2^a * b^2 for positive integers a, b.
    # Key insight: For any good integer X, we can write X = 2^a * b^2.
    # If we factor out all powers of 2 from b, we get b = 2^k * b_odd where b_odd is odd.
    # Then X = 2^a * (2^k * b_odd)^2 = 2^(a + 2k) * b_odd^2.
    # So every good integer can be uniquely represented as 2^A * b_odd^2 where b_odd is odd.
    # Thus, we only need to iterate over odd b values.
    # Also, a must be >= 1, so we start from a = 1.
    
    count = 0
    b = 1
    while True:
        b_sq = b * b
        if b_sq > N:
            break
        
        # For this odd b, count how many powers of 2 we can multiply by
        # such that 2^a * b_sq <= N, with a >= 1
        max_val = N // b_sq
        a = 1  # Start from 1, not 0
        while True:
            val = b_sq << a  # b_sq * 2^a
            if val > N:
                break
            count += 1
            a += 1
        
        b += 2  # Only odd b values
    
    return count

def main():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        N = int(line)
        result = count_good_integers(N)
        print(result)
    except Exception:
        pass

if __name__ == "__main__":
    main()
