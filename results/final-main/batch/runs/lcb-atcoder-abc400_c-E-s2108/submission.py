import sys
from math import isqrt

def solve():
    line = sys.stdin.read().strip()
    if not line:
        return
    N = int(line)
    
    # We need to count numbers X <= N such that X = 2^a * b^2
    # where a >= 1 and b >= 1 are integers.
    # 
    # Key insight: For any good integer X, we can write X = 2^a * b^2.
    # If b is even, say b = 2^k * m where m is odd, then b^2 = 2^(2k) * m^2.
    # So X = 2^a * 2^(2k) * m^2 = 2^(a+2k) * m^2.
    # This means we can always absorb all factors of 2 from b into the 2^a part.
    # 
    # Therefore, each good integer X corresponds uniquely to a pair (a, b) where b is odd.
    # 
    # So we need to count pairs (a, b) with a >= 1, b >= 1, b odd, such that:
    #   2^a * b^2 <= N
    # 
    # Let's iterate over possible values of b (odd only).
    # For each odd b, we need 2^a <= N / b^2, so a <= log2(N / b^2).
    # Since a >= 1, we need N / b^2 >= 2, i.e., b^2 <= N/2.
    # The number of valid a values is floor(log2(N / b^2)).
    # But we need to count how many integers a satisfy 1 <= a <= floor(log2(N / b^2)).
    # That's max(0, floor(log2(N / b^2))).
    # 
    # Alternatively, we can iterate over a and count odd b values.
    # For a fixed a, we need b^2 <= N / 2^a, so b <= sqrt(N / 2^a).
    # And b must be odd. The number of odd integers in [1, M] is (M + 1) // 2.
    
    count = 0
    power_of_2 = 2  # This is 2^a for a=1
    while power_of_2 <= N:
        limit = N // power_of_2
        if limit <= 0:
            break
        max_b = isqrt(limit)
        # Count odd b in [1, max_b]
        count += (max_b + 1) // 2
        # Prepare next power of 2
        if power_of_2 > N // 2:
            break
        power_of_2 *= 2
    
    print(count)

if __name__ == "__main__":
    solve()
