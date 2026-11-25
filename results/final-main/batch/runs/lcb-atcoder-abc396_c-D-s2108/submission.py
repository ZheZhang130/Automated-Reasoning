import sys
from typing import List

def solve() -> None:
    input_data = sys.stdin.read().split()
    if not input_data:
        return

    it = iter(input_data)
    N = int(next(it))
    M = int(next(it))

    B = []
    for _ in range(N):
        B.append(int(next(it)))

    W = []
    for _ in range(M):
        W.append(int(next(it)))

    # Sort both arrays in descending order to pick largest values first
    B.sort(reverse=True)
    W.sort(reverse=True)

    # We need to choose k black balls and k white balls (for some k >= 0)
    # plus possibly some additional black balls (since we can have more black than white)
    # plus possibly some additional white balls? No, we cannot have more white than black.
    # So the strategy:
    # For a fixed number of white balls w (0 <= w <= M), we must choose at least w black balls.
    # To maximize sum, we choose the w largest white balls.
    # For black balls, we choose the largest w black balls, and then we can also choose
    # any additional black balls that are positive (since adding a positive black ball
    # increases the sum and doesn't violate the constraint).
    # Actually, we can choose any number of black balls >= w.
    # So for a fixed w, we choose:
    #   - the w largest white balls (sum_W_w)
    #   - the largest w black balls (sum_B_w)
    #   - plus all black balls from index w to N-1 that are positive? 
    #     Actually, we can choose any subset of the remaining black balls (indices w to N-1)
    #     that are positive. But since we want to maximize, we should take all positive ones.
    #     However, note: we are allowed to choose MORE than w black balls.
    #     So for the remaining black balls (after taking the top w), we take all that are > 0.
    #     But wait: what if a black ball is negative? We don't have to take it.
    #     So for the remaining black balls (from index w to N-1), we take all that are > 0.
    #     However, note: we are not forced to take the top w black balls? 
    #     Actually, to maximize, we should take the largest black balls.
    #     So the strategy for a fixed w (number of white balls) is:
    #       Take the w largest white balls.
    #       Take the w largest black balls.
    #       Then, from the remaining black balls (which are the smallest w black balls, but we are allowed to take more),
    #       we take all the black balls that are positive? 
    #       But note: the remaining black balls (after taking the top w) are the ones from index w to N-1 (in sorted descending order).
    #       However, we are allowed to take ANY black balls as long as the total count of black balls >= w.
    #       So we take the top w black balls, and then we can also take any additional black balls that are positive.
    #       But the top w black balls are already the largest. The remaining black balls (from w to N-1) are smaller.
    #       So we should take all black balls from index w to N-1 that are positive? 
    #       Actually, we can take any subset of the remaining black balls. To maximize, we take all that are positive.
    #       However, note: the top w black balls are the largest, so they are definitely taken.
    #       The remaining black balls (from w to N-1) are the next largest. We take all that are positive.
    #       But what if a black ball at index w (0-indexed) is negative? Then we don't take it? 
    #       But we must take at least w black balls. So we take the top w black balls (which might include some negatives if necessary).
    #       Then for the remaining black balls (from w to N-1), we take all that are positive.
    #       However, note: the top w black balls are the largest w. The rest are smaller.
    #       So the algorithm for a fixed w:
    #         sum = sum of top w white balls
    #         sum += sum of top w black balls
    #         sum += sum of all black balls from index w to N-1 that are > 0
    #       But wait: the top w black balls are the largest w. The remaining black balls (from w to N-1) are the rest.
    #       We are allowed to take any number of black balls as long as >= w.
    #       So we take the top w black balls, and then we can take any additional black balls that are positive.
    #       However, the top w black balls are already taken. The remaining black balls (from w to N-1) are the ones we can optionally take.
    #       We take all of them that are positive.
    #       But note: the top w black balls might include some negatives? Only if we are forced to take them to meet the count w.
    #       However, if we are forced to take a negative black ball to meet the count w, then we have no choice for the first w.
    #       Then for the rest, we take all positives.
    #       So the formula for a fixed w is:
    #         base = sum(W[0:w]) + sum(B[0:w])
    #         plus sum(B[w:N]) for all elements > 0.
    #       But note: the top w black balls are B[0:w]. The rest are B[w:N].
    #       So we add the positive values in B[w:N].
    #       However, what if w=0? Then we take 0 white balls, and 0 black balls (minimum), and then we can take all positive black balls.
    #       So for w=0: base = 0, and we add all positive black balls.
    #       This matches.

    # Precompute prefix sums for W and B to quickly get sum of top w.
    # But note: we also need the sum of positive values in B[w:N].
    # We can precompute the suffix sum of positive values for B? 
    # Actually, we can compute an array for B: 
    #   Let P[i] = sum of B[j] for j from i to N-1 if B[j] > 0, else 0.
    # But note: we want the sum of positive values in B[w:N]. 
    # We can precompute an array S where S[i] = sum of positive values in B[i:].
    # Then for a fixed w, the additional black balls sum is S[w].

    # Steps:
    # 1. Sort B and W in descending order.
    # 2. Precompute prefix sums for W: W_prefix[i] = sum(W[0:i])
    # 3. Precompute an array for B: 
    #      We want for each starting index i, the sum of positive values in B[i:].
    #      We can do this by iterating from the end.
    #      Let B_suffix_positive[i] = sum of B[j] for j from i to N-1 if B[j] > 0.
    #      We can compute this by starting from the last element and going backwards.

    # However, note: the top w black balls are B[0:w]. The rest are B[w:N].
    # We take all positive values in B[w:N].

    # Let's compute:
    #   W_prefix: W_prefix[i] = sum(W[0:i]) for i from 0 to M+1.
    #   B_suffix_positive: an array of length N+1, where B_suffix_positive[i] = sum of positive values in B[i:].

    # Then for each w from 0 to min(N, M):
    #   current_sum = W_prefix[w] + (sum of B[0:w]) + B_suffix_positive[w]
    #   But note: the sum of B[0:w] is the prefix sum of B for w elements.
    #   However, we must be cautious: the prefix sum of B for w elements might include negatives? 
    #   But we are forced to take the top w black balls. So we take them regardless of sign.
    #   So we need the actual sum of B[0:w], not just the positive ones.

    # So we need:
    #   B_prefix[i] = sum(B[0:i]) for i from 0 to N+1.

    # Then for a fixed w:
    #   total = B_prefix[w] + W_prefix[w] + (sum of positive values in B[w:N])
    #   But note: the sum of positive values in B[w:N] is not simply B_prefix[N] - B_prefix[w] because we skip negatives.
    #   So we precompute B_suffix_positive as described.

    # Let's do it.

    # Precompute W_prefix
    W_prefix = [0] * (M + 1)
    current = 0
    for i in range(M):
        current += W[i]
        W_prefix[i+1] = current

    # Precompute B_prefix
    B_prefix = [0] * (N + 1)
    current = 0
    for i in range(N):
        current += B[i]
        B_prefix[i+1] = current

    # Precompute B_suffix_positive: 
    #   We want an array where suffix_positive[i] = sum of B[j] for j from i to N-1 if B[j] > 0.
    #   We can compute from the end.
    suffix_positive = [0] * (N + 1)
    current = 0
    for i in range(N-1, -1, -1):
        if B[i] > 0:
            current += B[i]
        suffix_positive[i] = current

    # Now iterate w from 0 to min(N, M)
    max_sum = -10**30  # a very small number

    # But note: we can also choose w=0, which is allowed.
    # Also, we must consider that we can choose w from 0 to min(N, M).

    for w in range(0, min(N, M) + 1):
        # Sum of top w white balls
        sum_W = W_prefix[w]
        # Sum of top w black balls
        sum_B_top = B_prefix[w]
        # Sum of positive black balls from index w to N-1
        sum_B_rest_positive = suffix_positive[w]
        total = sum_W + sum_B_top + sum_B_rest_positive
        if total > max_sum:
            max_sum = total

    # However, note: the problem allows choosing zero balls, which gives 0.
    # Our loop includes w=0, which gives:
    #   sum_W = 0
    #   sum_B_top = 0
    #   sum_B_rest_positive = sum of all positive black balls (since suffix_positive[0] is the sum of all positive black balls)
    # So for w=0, total = sum of all positive black balls.
    # But what if all black balls are negative? Then suffix_positive[0] = 0, so total=0.
    # And we can choose zero balls -> 0.
    # So our method for w=0 gives the maximum we can get with 0 white balls and any number of black balls (only positives).
    # But note: we are allowed to choose zero balls, which is 0. Our method for w=0 might give a positive number if there are positive black balls.
    # However, if there are no positive black balls, then w=0 gives 0, which is correct.
    # But what if we choose some negative black balls? We are not forced to, because we can choose zero balls (which is 0) or only positive black balls.
    # So our method is correct.

    # However, note: the problem says "choose zero or more balls". Our method for w=0 considers choosing only positive black balls (and zero white balls).
    # But we are also allowed to choose zero balls (which is 0). Our method for w=0 gives the sum of positive black balls, which is >=0.
    # So it's safe.

    # But wait: what if the maximum is achieved by choosing some negative black balls? 
    # Actually, we never want to choose a negative black ball if we can avoid it, because it reduces the sum.
    # However, we are forced to choose at least w black balls. So for a fixed w, we must choose the top w black balls (which might include negatives).
    # Then we can choose additional black balls that are positive.
    # So our method is correct.

    # However, note: the problem does not require that we choose contiguous balls. But since we sort, the top w are the best.
    # So the algorithm is correct.

    # But wait: what if we choose w white balls and w black balls, and then we don't choose any additional black balls? 
    # Our method includes the additional positive black balls. But what if we don't want to choose them? 
    # Actually, we always want to choose them if they are positive, because they increase the sum.
    # And if they are negative, we don't choose them (because suffix_positive only adds positives).
    # So it's correct.

    # However, note: the problem allows choosing any subset. Our method for a fixed w chooses:
    #   - the best w white balls
    #   - the best w black balls (to meet the count constraint)
    #   - and then all additional black balls that are positive (because they are beneficial)
    # This is optimal for a fixed w.

    # But what if we choose more than w black balls? We are allowed to. And we do by taking the positive ones.
    # So the algorithm is correct.

    # However, note: the problem says "at least the number of white balls chosen". So we can choose more black balls.
    # And we do by taking the positive ones.

    # One more thing: what if we choose w white balls and w black balls, and then we choose some negative black balls? 
    # We don't, because that would reduce the sum. So we only choose positive additional black balls.

    # Therefore, the above loop is correct.

    # But note: the problem allows choosing zero balls. Our method for w=0 gives the sum of all positive black balls (if any) and 0 otherwise.
    # And if there are no positive black balls, then w=0 gives 0, which is the same as choosing zero balls.
    # So it's covered.

    # However, what if the maximum is achieved by choosing some white balls and some black balls, but not the top w white balls? 
    # No, because we sort W in descending order, so the top w are the best.

    # Similarly for black balls: the top w are the best for the mandatory part, and then we take the positive ones from the rest.

    # So the algorithm is correct.

    # But note: the constraints say N, M up to 200,000. Our solution is O(N log N + M log M) due to sorting, and then O(N+M) for the rest.
    # This is efficient.

    # Print the answer.
    print(max_sum)

if __name__ == '__main__':
    solve()
