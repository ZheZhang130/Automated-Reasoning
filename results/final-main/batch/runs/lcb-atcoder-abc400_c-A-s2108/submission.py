import sys
from math import isqrt

def solve():
    line = sys.stdin.read().strip()
    if not line:
        return
    N = int(line)
    
    # We need to count unique X <= N such that X = 2^a * b^2
    # where a >= 1 and b >= 1 are integers.
    # 
    # Approach: For each b, we can have X = 2^a * b^2 for various a.
    # But different (a, b) pairs can give the same X.
    # 
    # Key insight: For a given X, if X = 2^a * b^2, then:
    # - The odd part of X must be a perfect square (since b^2 contributes the odd part)
    # - The power of 2 in X must be at least 1
    # 
    # Let's enumerate by the "square part" b^2 and the power of 2.
    # For each b, we can have X = 2^a * b^2 for a = 1, 2, 3, ...
    # But we need to avoid double-counting.
    # 
    # Alternative approach: For each possible b, compute b^2, then multiply by 2^a
    # for a = 1, 2, ... as long as the result <= N.
    # Use a set to track unique values.
    
    seen = set()
    b = 1
    while True:
        b2 = b * b
        if b2 > N:
            break
        # For this b, we can have X = 2^a * b^2 for a = 1, 2, ...
        power_of_2 = 2
        while power_of_2 * b2 <= N:
            seen.add(power_of_2 * b2)
            # Check for overflow before multiplying
            if power_of_2 > N // 2:
                break
            power_of_2 *= 2
        b += 1
        if b > 1000000000:  # Safety check
            break
    
    print(len(seen))

if __name__ == "__main__":
    solve()
