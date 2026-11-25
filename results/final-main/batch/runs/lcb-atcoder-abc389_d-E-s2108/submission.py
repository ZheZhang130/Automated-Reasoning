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

    # We need to count integer pairs (i, j) such that the square with corners
    # (i+/-0.5, j+/-0.5) is inside the circle of radius R centered at (0,0).
    # The condition is that the farthest corner from the origin is within distance R.
    # The farthest corner from (0,0) for a square centered at (i,j) is at distance
    # sqrt((|i|+0.5)^2 + (|j|+0.5)^2).
    # So we need (|i|+0.5)^2 + (|j|+0.5)^2 <= R^2.
    # By symmetry, we can count for i >= 0, j >= 0 and multiply appropriately.
    # For i=0, j=0: 1 square
    # For i=0, j>0: 4 squares (symmetric in j)
    # For i>0, j=0: 4 squares (symmetric in i)
    # For i>0, j>0: 4 squares (symmetric in both)
    
    # Actually, let's think more carefully.
    # The squares are indexed by their center (i, j) where i and j are integers.
    # The square centered at (i, j) has corners at (i+/-0.5, j+/-0.5).
    # The farthest corner from (0,0) is at distance sqrt((|i|+0.5)^2 + (|j|+0.5)^2).
    # We need this distance <= R.
    
    # Let's count by iterating over possible values of i and j.
    # Since R can be up to 10^6, we need an efficient approach.
    # However, the condition (|i|+0.5)^2 + (|j|+0.5)^2 <= R^2 defines a region.
    # We can iterate over i from -floor(R-0.5) to floor(R-0.5) and for each i,
    # find the range of j values.
    
    # Actually, let's use symmetry. We can count for i >= 0, j >= 0 and then multiply.
    # But we need to be careful about the boundaries.
    
    # Let's define the condition more precisely:
    # (|i|+0.5)^2 + (|j|+0.5)^2 <= R^2
    # Let a = |i|, b = |j|. Then (a+0.5)^2 + (b+0.5)^2 <= R^2.
    # We need to count the number of pairs (a, b) with a, b >= 0 integers satisfying this.
    # Then we need to account for the signs of i and j.
    
    # For a = 0, b = 0: only (0, 0) -> 1 square
    # For a = 0, b > 0: (0, b) and (0, -b) -> 2 squares for each b
    # For a > 0, b = 0: (a, 0) and (-a, 0) -> 2 squares for each a
    # For a > 0, b > 0: (a, b), (a, -b), (-a, b), (-a, -b) -> 4 squares for each (a, b)
    
    # So the total count is:
    # 1 (for a=0, b=0) 
    # + 2 * (number of b > 0 such that (0+0.5)^2 + (b+0.5)^2 <= R^2)
    # + 2 * (number of a > 0 such that (a+0.5)^2 + (0+0.5)^2 <= R^2)
    # + 4 * (number of pairs (a, b) with a > 0, b > 0 such that (a+0.5)^2 + (b+0.5)^2 <= R^2)
    
    # Let's simplify:
    # Let a' = a + 0.5, b' = b + 0.5. Then a' and b' are half-integers >= 0.5.
    # The condition is a'^2 + b'^2 <= R^2.
    # We can iterate over a' from 0.5 to R-0.5 (since b' >= 0.5, a' <= R-0.5).
    # For each a', we find the maximum b' such that b'^2 <= R^2 - a'^2.
    # Then b' can take values from 0.5 to floor(sqrt(R^2 - a'^2)) + 0.5.
    # But we need to be careful about the counting.
    
    # Alternative approach:
    # Iterate over i from -floor(R-0.5) to floor(R-0.5).
    # For each i, find the range of j values.
    # The condition is (|i|+0.5)^2 + (|j|+0.5)^2 <= R^2.
    # Let a = |i|. Then (a+0.5)^2 + (|j|+0.5)^2 <= R^2.
    # So (|j|+0.5)^2 <= R^2 - (a+0.5)^2.
    # Let rhs = R^2 - (a+0.5)^2.
    # If rhs < 0.25, then no j exists (since (|j|+0.5)^2 >= 0.25).
    # Otherwise, |j|+0.5 <= sqrt(rhs).
    # So |j| <= sqrt(rhs) - 0.5.
    # Let max_j = floor(sqrt(rhs) - 0.5).
    # Then j can range from -max_j to max_j, which is 2*max_j + 1 values.
    # But we need to be careful: if max_j < 0, then there are no j values.
    
    # Actually, let's think again.
    # The condition is (|i|+0.5)^2 + (|j|+0.5)^2 <= R^2.
    # For a fixed i, let a = |i|. Then (a+0.5)^2 + (|j|+0.5)^2 <= R^2.
    # So (|j|+0.5)^2 <= R^2 - (a+0.5)^2.
    # Let rhs = R^2 - (a+0.5)^2.
    # If rhs < 0.25, then no j exists.
    # Otherwise, |j|+0.5 <= sqrt(rhs).
    # So |j| <= sqrt(rhs) - 0.5.
    # Let max_j = floor(sqrt(rhs) - 0.5).
    # If max_j < 0, then there are no j values.
    # Otherwise, j can range from -max_j to max_j, which is 2*max_j + 1 values.
    
    # But wait, we need to be careful about the case when i = 0.
    # When i = 0, a = 0, and the condition is (0+0.5)^2 + (|j|+0.5)^2 <= R^2.
    # So 0.25 + (|j|+0.5)^2 <= R^2.
    # (|j|+0.5)^2 <= R^2 - 0.25.
    # |j|+0.5 <= sqrt(R^2 - 0.25).
    # |j| <= sqrt(R^2 - 0.25) - 0.5.
    # Let max_j = floor(sqrt(R^2 - 0.25) - 0.5).
    # Then j can range from -max_j to max_j, which is 2*max_j + 1 values.
    
    # Similarly, for i != 0, we have a = |i| > 0.
    # The condition is (a+0.5)^2 + (|j|+0.5)^2 <= R^2.
    # (|j|+0.5)^2 <= R^2 - (a+0.5)^2.
    # |j|+0.5 <= sqrt(R^2 - (a+0.5)^2).
    # |j| <= sqrt(R^2 - (a+0.5)^2) - 0.5.
    # Let max_j = floor(sqrt(R^2 - (a+0.5)^2) - 0.5).
    # If max_j < 0, then there are no j values.
    # Otherwise, j can range from -max_j to max_j, which is 2*max_j + 1 values.
    
    # Now, we need to sum over all i from -floor(R-0.5) to floor(R-0.5).
    # But by symmetry, we can compute for i >= 0 and then multiply appropriately.
    # For i = 0: count = 2*max_j + 1.
    # For i > 0: count = 2*max_j + 1, and there are two such i values (i and -i).
    # So total = (2*max_j_0 + 1) + 2 * sum_{i=1}^{floor(R-0.5)} (2*max_j_i + 1).
    
    # Let's implement this.
    
    R_sq = R * R
    
    # Maximum possible |i| is floor(R - 0.5).
    # Since i is integer, |i| <= floor(R - 0.5).
    # Actually, let's think: (|i|+0.5)^2 <= R^2 - 0.25.
    # So |i|+0.5 <= sqrt(R^2 - 0.25).
    # |i| <= sqrt(R^2 - 0.25) - 0.5.
    # Let max_i = floor(sqrt(R^2 - 0.25) - 0.5).
    # If max_i < 0, then there are no i values.
    
    # Actually, let's just iterate over i from -max_i to max_i.
    # But we can use symmetry.
    
    # Let's compute for i >= 0.
    # For i = 0:
    #   rhs = R_sq - 0.25
    #   max_j = floor(sqrt(rhs) - 0.5)
    #   count_0 = 2 * max_j + 1
    # For i > 0:
    #   a = i
    #   rhs = R_sq - (a + 0.5)**2
    #   if rhs < 0.25:
    #       count_i = 0
    #   else:
    #       max_j = floor(sqrt(rhs) - 0.5)
    #       count_i = 2 * max_j + 1
    #   total += count_i
    # Then total = count_0 + 2 * sum_{i=1}^{max_i} count_i
    
    # But wait, we need to be careful about the maximum i.
    # The maximum i is such that (i+0.5)^2 <= R^2 - 0.25.
    # So i+0.5 <= sqrt(R^2 - 0.25).
    # i <= sqrt(R^2 - 0.25) - 0.5.
    # Let max_i = floor(sqrt(R^2 - 0.25) - 0.5).
    # If max_i < 0, then there are no i values.
    
    # Actually, let's just iterate over i from 0 to max_i.
    # For i = 0, we compute count_0.
    # For i > 0, we compute count_i and add 2 * count_i to the total.
    
    # Let's implement this.
    
    import math
    
    # Maximum i such that (i+0.5)^2 <= R^2 - 0.25
    # i+0.5 <= sqrt(R^2 - 0.25)
    # i <= sqrt(R^2 - 0.25) - 0.5
    max_i = int(math.sqrt(R_sq - 0.25) - 0.5)
    
    if max_i < 0:
        print(0)
        return
    
    total = 0
    
    # For i = 0
    rhs = R_sq - 0.25
    max_j = int(math.sqrt(rhs) - 0.5)
    if max_j < 0:
        max_j = -1
    count_0 = 2 * max_j + 1
    total += count_0
    
    # For i > 0
    for i in range(1, max_i + 1):
        a = i
        rhs = R_sq - (a + 0.5)**2
        if rhs < 0.25:
            continue
        max_j = int(math.sqrt(rhs) - 0.5)
        if max_j < 0:
            max_j = -1
        count_i = 2 * max_j + 1
        total += 2 * count_i
    
    print(total)

solve()
