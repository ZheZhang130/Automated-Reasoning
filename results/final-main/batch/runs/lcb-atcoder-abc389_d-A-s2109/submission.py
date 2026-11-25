import sys
import math

def solve():
    line = sys.stdin.read().strip()
    if not line:
        return
    R = int(line)
    
    # We need to count integer pairs (i, j) such that the square with corners
    # (i+/-0.5, j+/-0.5) is inside the circle of radius R centered at (0,0).
    # The condition is that the farthest corner from the origin is within distance R.
    # The farthest corner from (0,0) for a square centered at (i,j) is at distance:
    # sqrt((i+0.5)^2 + (j+0.5)^2) if i,j >= 0 (in the first quadrant relative to center)
    # Actually, the farthest point from origin for a square centered at (i,j) is:
    # sign(i)*0.5 + sign(j)*0.5 added to |i| and |j| respectively.
    # So the condition is: (|i| + 0.5)^2 + (|j| + 0.5)^2 <= R^2
    
    # We can iterate over i from 0 to floor(R - 0.5)
    # For each i, we find the range of j such that (|i| + 0.5)^2 + (|j| + 0.5)^2 <= R^2
    # Since the problem is symmetric, we can compute for i >= 0 and j >= 0 and multiply appropriately.
    
    # Let's define:
    # For a given i (>=0), we need (i + 0.5)^2 + (j + 0.5)^2 <= R^2
    # => (j + 0.5)^2 <= R^2 - (i + 0.5)^2
    # => j + 0.5 <= sqrt(R^2 - (i + 0.5)^2)
    # => j <= sqrt(R^2 - (i + 0.5)^2) - 0.5
    
    # So for each i from 0 to some max, we compute the max j (>=0) and then count the number of j's.
    # The number of non-negative j's is floor(max_j) + 1, where max_j = sqrt(...) - 0.5
    
    # But we need to be careful: the condition is for the square to be inside, so we need the farthest corner.
    # For a square centered at (i, j), the farthest corner from origin is at:
    # (sign(i)*0.5 + |i|, sign(j)*0.5 + |j|) = (|i| + 0.5, |j| + 0.5) if we consider the corner in the same quadrant.
    # So the condition is indeed (|i| + 0.5)^2 + (|j| + 0.5)^2 <= R^2.
    
    # We'll iterate i from 0 to R (since i+0.5 <= R => i <= R-0.5, so i goes up to floor(R-0.5))
    # Actually, i can go up to floor(R - 0.5). Let's compute the max i:
    # i + 0.5 <= R => i <= R - 0.5 => max_i = floor(R - 0.5)
    
    max_i = int(R - 0.5)
    
    count = 0
    R_sq = R * R
    
    for i in range(max_i + 1):
        # Compute the max (j + 0.5)^2
        rem = R_sq - (i + 0.5)**2
        if rem < 0:
            break
        max_j_plus_05 = math.sqrt(rem)
        max_j = max_j_plus_05 - 0.5
        # The number of non-negative j's is floor(max_j) + 1
        num_j = int(max_j) + 1
        count += num_j
    
    # Now, for each i > 0, we have symmetric j values (positive and negative).
    # For i = 0, j can be positive, negative, and zero.
    # But our count above for i=0 includes j=0 and positive j's.
    # We need to account for symmetry:
    # For i > 0, each positive j corresponds to a negative j, so we multiply by 2.
    # For i = 0, we have j=0 (counted once) and positive j's (each has a negative counterpart).
    
    # Let's recompute:
    # For i = 0: count includes j from 0 to max_j (inclusive). 
    #   The number of j's is num_j (which includes j=0 and positive j's).
    #   The symmetric negative j's are not included. So for i=0, we need to add the negative j's.
    #   But note: the set of j's for i=0 is symmetric around 0. So if we have k positive j's and one zero,
    #   then the total count for i=0 is 2*k + 1. Our num_j for i=0 is k+1 (including zero and k positive).
    #   So we need to subtract the zero and the positive j's and then double the positive j's and add the zero?
    #   Actually, let's think differently.
    
    # Alternative approach:
    # For each i from 0 to max_i, we compute the number of j's (both positive and negative) that satisfy the condition.
    # For a given i, the condition is (i+0.5)^2 + (j+0.5)^2 <= R^2 for j>=0, and similarly for j<0.
    # But note: the condition for j<0 is the same as for j>0 because of symmetry? 
    # Actually, the condition for a square centered at (i, j) is (|i|+0.5)^2 + (|j|+0.5)^2 <= R^2.
    # So for a fixed i (>=0), the condition on j is (|j|+0.5)^2 <= R^2 - (i+0.5)^2.
    # Let M = sqrt(R^2 - (i+0.5)^2) - 0.5. Then |j| <= M.
    # So j can be in [-floor(M), floor(M)].
    # The number of such j's is 2*floor(M) + 1.
    
    # But wait: our previous count for i=0 was num_j = floor(M) + 1 (for j>=0). 
    # The total count for i=0 should be 2*floor(M) + 1.
    # Similarly for i>0, the total count is 2*floor(M) + 1.
    
    # So we can recompute:
    # For each i from 0 to max_i:
    #   M = sqrt(R^2 - (i+0.5)^2) - 0.5
    #   num_j = 2 * floor(M) + 1
    #   count += num_j
    
    # Let's test with R=2:
    # max_i = floor(2-0.5) = 1.
    # i=0: rem = 4 - 0.25 = 3.75, M = sqrt(3.75)-0.5 ≈ 1.936 - 0.5 = 1.436, floor(M)=1, num_j=3.
    # i=1: rem = 4 - 2.25 = 1.75, M = sqrt(1.75)-0.5 ≈ 1.323 - 0.5 = 0.823, floor(M)=0, num_j=1.
    # Total = 3+1 = 4. But expected is 5.
    
    # What's wrong? 
    # The issue is that for i=0, the squares are centered at (0, j). The condition is (0+0.5)^2 + (|j|+0.5)^2 <= 4.
    # For j=0: (0.5)^2 + (0.5)^2 = 0.5 <= 4 -> valid.
    # For j=1: (0.5)^2 + (1.5)^2 = 0.25+2.25=2.5 <=4 -> valid.
    # For j=-1: same as j=1 -> valid.
    # For j=2: (0.5)^2 + (2.5)^2 = 0.25+6.25=6.5 >4 -> invalid.
    # So for i=0, j in {-1,0,1} -> 3 squares.
    # For i=1: (1+0.5)^2 + (|j|+0.5)^2 <=4 -> 2.25 + (|j|+0.5)^2 <=4 -> (|j|+0.5)^2 <=1.75 -> |j|+0.5 <= sqrt(1.75)≈1.323 -> |j|<=0.823 -> j=0 only.
    # For i=-1: same as i=1 -> 1 square.
    # Total = 3 (i=0) + 1 (i=1) + 1 (i=-1) = 5. Correct.
    
    # So the formula for each i (from -max_i to max_i) is the same as for |i|.
    # We can compute for i from 0 to max_i, and then for i>0, multiply by 2, and for i=0, use as is.
    # But note: our loop for i from 0 to max_i gives the count for i=0 and i>0. Then we need to add the symmetric i<0.
    # Actually, we can do:
    #   count = 0
    #   for i in range(0, max_i+1):
    #       M = sqrt(R^2 - (i+0.5)^2) - 0.5
    #       num_j = 2 * floor(M) + 1
    #       if i == 0:
    #           count += num_j
    #       else:
    #           count += 2 * num_j   # because i and -i are distinct and both have the same count
    # But wait, that would double count i=0? No, because i=0 is only once.
    # However, note that for i>0, we are adding the count for i and -i together (which is 2 * num_j).
    # And for i=0, we add num_j (which is the count for i=0, which is symmetric in j).
    
    # Let's test with R=2 again:
    # i=0: num_j = 3, count=3.
    # i=1: num_j = 1, count=3 + 2*1 = 5. Correct.
    
    # So the corrected code:
    
    count = 0
    for i in range(max_i + 1):
        rem = R_sq - (i + 0.5)**2
        if rem < 0:
            break
        max_j_plus_05 = math.sqrt(rem)
        max_j = max_j_plus_05 - 0.5
        num_j = 2 * int(max_j) + 1
        if i == 0:
            count += num_j
        else:
            count += 2 * num_j
    
    print(count)

if __name__ == '__main__':
    solve()
