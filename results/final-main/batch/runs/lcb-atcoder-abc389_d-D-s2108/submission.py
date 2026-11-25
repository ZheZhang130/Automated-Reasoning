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

    # For a square centered at (i, j), the farthest corner from origin is at distance sqrt((|i|+0.5)^2 + (|j|+0.5)^2)
    # We need this distance <= R.
    # By symmetry, we can count for i >= 0 and j >= 0, then multiply appropriately.
    # Actually, we can iterate over possible i values and for each i, count valid j's.
    # The condition is: (|i| + 0.5)^2 + (|j| + 0.5)^2 <= R^2
    # Let x = |i| + 0.5, y = |j| + 0.5. Then x^2 + y^2 <= R^2.
    # For a fixed x, y <= sqrt(R^2 - x^2).
    # Since y = |j| + 0.5, we have |j| + 0.5 <= sqrt(R^2 - x^2)
    # => |j| <= sqrt(R^2 - x^2) - 0.5
    # => j_max = floor(sqrt(R^2 - x^2) - 0.5)
    # The number of non-negative j values is j_max + 1 (including j=0).
    # But we need to be careful: if j_max < 0, then no non-negative j exists.

    R_sq = R * R
    count = 0

    # i ranges from -(R-0.5) to (R-0.5). Since |i| + 0.5 <= R, |i| <= R - 0.5.
    # So |i| can be from 0 to floor(R - 0.5).
    # Let's iterate i from 0 to floor(R - 0.5).
    # For each i, x = i + 0.5
    # Then max_y = sqrt(R_sq - x^2)
    # Then max_j = floor(max_y - 0.5)
    # Number of j values for this |i| is max_j + 1 (if max_j >= 0) else 0.
    # But we have to account for symmetry:
    # If i = 0, then there is only one i value (0), and j can be positive, negative, or zero.
    # If i > 0, then there are two i values (i and -i), and for each, j can be positive, negative, or zero.
    # Actually, let's restructure:
    # We iterate over possible values of |i| from 0 to floor(R - 0.5).
    # For each |i|, we compute the number of valid |j| values.
    # Then we multiply by 2 if |i| > 0, else 1.
    # For each |i|, the number of valid |j| values is:
    #   Let x = |i| + 0.5
    #   Let max_y = sqrt(R_sq - x^2)
    #   Let max_j = floor(max_y - 0.5)
    #   If max_j < 0, then 0 valid |j| values.
    #   Else, the number of non-negative |j| values is max_j + 1.
    # But wait, |j| can be 0, 1, ..., max_j. So there are max_j + 1 values.
    # However, we must ensure that for each |j|, the actual j values are:
    #   If |j| = 0, then j = 0 (1 value)
    #   If |j| > 0, then j = |j| and j = -|j| (2 values)
    # So for a fixed |i|, the total number of j values is:
    #   1 (for j=0) + 2 * (number of positive |j| values)
    #   = 1 + 2 * max_j   (if max_j >= 0)
    # But this is only if we consider all j for a fixed |i|.
    # Actually, let's do it differently:
    # For a fixed |i|, the condition on j is:
    #   (|i| + 0.5)^2 + (|j| + 0.5)^2 <= R^2
    #   => (|j| + 0.5)^2 <= R^2 - (|i| + 0.5)^2
    #   => |j| + 0.5 <= sqrt(R^2 - (|i| + 0.5)^2)
    #   => |j| <= sqrt(R^2 - (|i| + 0.5)^2) - 0.5
    # Let max_j_val = floor(sqrt(R^2 - (|i| + 0.5)^2) - 0.5)
    # Then |j| can be 0, 1, ..., max_j_val.
    # For |j| = 0, j = 0 (1 value)
    # For |j| = k > 0, j = k and j = -k (2 values)
    # So total j values for fixed |i| is: 1 + 2 * max_j_val (if max_j_val >= 0)
    # But note: if max_j_val < 0, then there are no j values.

    # However, we must also consider that |i| can be 0.
    # So we iterate |i| from 0 to floor(R - 0.5).
    # But note: |i| + 0.5 <= R => |i| <= R - 0.5 => |i| <= floor(R - 0.5)
    # Since R is integer, floor(R - 0.5) = R - 1.
    # So |i| ranges from 0 to R-1.

    max_i = R - 1
    for i_abs in range(0, max_i + 1):
        x = i_abs + 0.5
        rem = R_sq - x*x
        if rem < 0:
            break
        max_y = math.sqrt(rem)
        max_j_val = max_y - 0.5
        if max_j_val < 0:
            continue
        max_j_val = int(max_j_val)  # floor
        if max_j_val < 0:
            max_j_val = -1
        num_j = 1 + 2 * max_j_val
        if i_abs == 0:
            count += num_j
        else:
            count += 2 * num_j

    print(count)

if __name__ == "__main__":
    solve()
