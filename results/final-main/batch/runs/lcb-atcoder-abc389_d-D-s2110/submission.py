import sys
import math

def solve():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        R = int(line)
    except ValueError:
        return

    # For a square centered at (i, j) to be completely inside the circle of radius R,
    # all four corners must be within distance R from the origin.
    # The corners are (i+0.5, j+0.5), (i+0.5, j-0.5), (i-0.5, j+0.5), (i-0.5, j-0.5).
    # The farthest corner from the origin for a given (i, j) is at distance sqrt((|i|+0.5)^2 + (|j|+0.5)^2).
    # So the condition is: (|i| + 0.5)^2 + (|j| + 0.5)^2 <= R^2.
    # Let x = |i| + 0.5, y = |j| + 0.5. Then x^2 + y^2 <= R^2.
    # Since x and y are half-integers (k + 0.5), we can multiply by 2 to work with integers.
    # Let X = 2*|i| + 1, Y = 2*|j| + 1. Then (X/2)^2 + (Y/2)^2 <= R^2  =>  X^2 + Y^2 <= 4*R^2.
    # We need to count the number of pairs (i, j) such that X = 2*|i|+1, Y = 2*|j|+1 satisfy X^2 + Y^2 <= 4*R^2.
    # Note that X and Y are odd positive integers.
    # For each valid (X, Y) with X, Y odd and X^2 + Y^2 <= 4*R^2, we need to count how many (i, j) map to it.
    # Since X = 2*|i|+1, |i| = (X-1)/2. So for a given X, there is exactly one |i|, and thus 2 choices for i (positive and negative), unless i=0.
    # Similarly for j.
    # If i=0, then X=1, and there is only 1 choice for i.
    # If i!=0, then there are 2 choices for i.
    # Same for j.
    # So for a pair (X, Y), the number of (i, j) is:
    #   (1 if X==1 else 2) * (1 if Y==1 else 2)
    # But note: X and Y are determined by |i| and |j|. We are iterating over |i| and |j|, so we can iterate over non-negative i and j.
    # Actually, it's easier to iterate over i from 0 to some max, and for each i, find the range of j.
    # Condition: (|i| + 0.5)^2 + (|j| + 0.5)^2 <= R^2
    # => (|j| + 0.5)^2 <= R^2 - (|i| + 0.5)^2
    # => |j| + 0.5 <= sqrt(R^2 - (|i| + 0.5)^2)
    # => |j| <= sqrt(R^2 - (|i| + 0.5)^2) - 0.5
    # Let max_j_val = floor(sqrt(R^2 - (|i| + 0.5)^2) - 0.5)
    # Then for a fixed |i|, the number of j values is:
    #   If max_j_val < 0, then 0.
    #   Else, the number of non-negative j is max_j_val + 1 (j from 0 to max_j_val).
    #   But we must account for the sign of j.
    #   If j=0, only 1 choice. If j>0, 2 choices (positive and negative).
    #   So for a fixed |i|, let j_max = floor(sqrt(R^2 - (|i| + 0.5)^2) - 0.5).
    #   If j_max < 0, count = 0.
    #   Else, count for j=0 is 1 (if 0 <= j_max).
    #   Count for j from 1 to j_max is 2 * j_max.
    #   Total for fixed |i| = 1 + 2 * j_max (if j_max >= 0).
    #   But wait, if j_max < 0, then we have 0.
    #   So: if j_max < 0: 0; else: 1 + 2 * j_max.
    # Now, for |i|, we have:
    #   If i=0, then |i|=0, and we have 1 choice for i.
    #   If i>0, then |i|=i, and we have 2 choices for i (positive and negative).
    # So we can iterate i from 0 to some max_i.
    # Max i: (|i| + 0.5)^2 <= R^2 => |i| + 0.5 <= R => |i| <= R - 0.5 => |i| <= floor(R - 0.5).
    # Since i is integer, max_i = floor(R - 0.5) = R - 1 (since R is integer, R-0.5 is not integer, floor is R-1).
    # Actually, let's check: if R=2, max_i = floor(1.5) = 1. So i from 0 to 1.
    # For i=0: |i|=0.
    # For i=1: |i|=1.
    # So we iterate i from 0 to R-1 (inclusive).
    # For each i, compute max_j_val = floor(sqrt(R^2 - (i + 0.5)^2) - 0.5).
    # If max_j_val < 0, then count for this i is 0.
    # Else, count for this i = (1 if i==0 else 2) * (1 + 2 * max_j_val).
    # But wait, the formula for j count: 
    #   j=0: 1 choice.
    #   j=1 to max_j_val: 2 * max_j_val choices.
    #   Total: 1 + 2 * max_j_val.
    # So total count = (1 if i==0 else 2) * (1 + 2 * max_j_val) if max_j_val >= 0 else 0.
    # However, note that if max_j_val < 0, then 1 + 2*max_j_val might be <=0, but we should take max(0, ...).
    # Actually, if max_j_val < 0, then 1 + 2*max_j_val might be 0 or negative. But we want 0.
    # So: count_i = (1 if i==0 else 2) * max(0, 1 + 2 * max_j_val)
    # But note: if max_j_val < 0, then 1 + 2*max_j_val <= 0, so max(0, ...) gives 0.
    # However, we must be cautious: if max_j_val is negative, then 1+2*max_j_val might be negative, but we want 0.
    # So: count_i = (1 if i==0 else 2) * max(0, 1 + 2 * max_j_val)
    # But wait, what if max_j_val is -0.5? Then 1+2*(-0.5)=0, so max(0,0)=0. Correct.
    # What if max_j_val is -1? Then 1+2*(-1)=-1, max(0,-1)=0. Correct.
    # So the formula is safe.

    # However, let's test with R=2.
    # i from 0 to 1.
    # i=0: |i|=0.
    #   term = (0+0.5)^2 = 0.25.
    #   R^2 - term = 4 - 0.25 = 3.75.
    #   sqrt(3.75) ≈ 1.936.
    #   max_j_val = floor(1.936 - 0.5) = floor(1.436) = 1.
    #   count for i=0: (1) * (1 + 2*1) = 3.
    # i=1: |i|=1.
    #   term = (1+0.5)^2 = 2.25.
    #   R^2 - term = 4 - 2.25 = 1.75.
    #   sqrt(1.75) ≈ 1.322.
    #   max_j_val = floor(1.322 - 0.5) = floor(0.822) = 0.
    #   count for i=1: (2) * (1 + 2*0) = 2.
    # Total = 3 + 2 = 5. Correct.

    # R=4:
    # i from 0 to 3.
    # i=0: |i|=0.
    #   term = 0.25.
    #   R^2 - term = 16 - 0.25 = 15.75.
    #   sqrt(15.75) ≈ 3.968.
    #   max_j_val = floor(3.968 - 0.5) = floor(3.468) = 3.
    #   count = 1 * (1 + 6) = 7.
    # i=1: |i|=1.
    #   term = 2.25.
    #   R^2 - term = 16 - 2.25 = 13.75.
    #   sqrt(13.75) ≈ 3.708.
    #   max_j_val = floor(3.708 - 0.5) = floor(3.208) = 3.
    #   count = 2 * (1 + 6) = 14.
    # i=2: |i|=2.
    #   term = 6.25.
    #   R^2 - term = 16 - 6.25 = 9.75.
    #   sqrt(9.75) ≈ 3.122.
    #   max_j_val = floor(3.122 - 0.5) = floor(2.622) = 2.
    #   count = 2 * (1 + 4) = 10.
    # i=3: |i|=3.
    #   term = 12.25.
    #   R^2 - term = 16 - 12.25 = 3.75.
    #   sqrt(3.75) ≈ 1.936.
    #   max_j_val = floor(1.936 - 0.5) = floor(1.436) = 1.
    #   count = 2 * (1 + 2) = 6.
    # Total = 7 + 14 + 10 + 6 = 37. Correct.

    total = 0
    R_sq = R * R
    # i from 0 to R-1 (since |i| <= R-0.5, and i integer, so i <= R-1)
    for i in range(R):
        # |i| = i
        term_i = (i + 0.5) ** 2
        rem = R_sq - term_i
        if rem < 0:
            # This should not happen for i < R, but for safety
            continue
        sqrt_rem = math.sqrt(rem)
        max_j_val = int(sqrt_rem - 0.5)  # floor
        if max_j_val < 0:
            count_i = 0
        else:
            count_i = 1 + 2 * max_j_val
        multiplier = 1 if i == 0 else 2
        total += multiplier * count_i

    print(total)

if __name__ == "__main__":
    solve()
