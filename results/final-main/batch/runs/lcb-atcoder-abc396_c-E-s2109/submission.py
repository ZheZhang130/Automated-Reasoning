import sys
from typing import List

def solve() -> None:
    input_data = sys.stdin.read().split()
    if not input_data:
        return

    iterator = iter(input_data)
    N = int(next(iterator))
    M = int(next(iterator))

    B = []
    for _ in range(N):
        B.append(int(next(iterator)))

    W = []
    for _ in range(M):
        W.append(int(next(iterator)))

    # Sort both arrays in descending order to pick largest values first
    B.sort(reverse=True)
    W.sort(reverse=True)

    # We need to choose k black balls and k white balls for some k >= 0
    # Or choose k black balls and j white balls where k >= j
    # Strategy:
    # 1. Consider taking i black balls and i white balls (for i from 0 to min(N, M))
    #    Sum = sum(B[:i]) + sum(W[:i])
    # 2. Consider taking i black balls and j white balls where j < i
    #    We should take all positive white balls, but limited by j < i
    #    Actually, a better approach:
    #    Let's iterate on the number of black balls we take: k (from 0 to N)
    #    For a fixed k, we can take at most k white balls.
    #    To maximize sum, we take the top min(k, M) white balls, but only if they are positive?
    #    No, we can take negative white balls if we are forced to balance, but since we want max sum,
    #    we should only take white balls that are positive, up to k.
    #    However, the constraint is: count(black) >= count(white).
    #    So if we take k black balls, we can take any number of white balls from 0 to min(k, M).
    #    To maximize, we take the top min(k, M) white balls, but only those that are positive?
    #    Actually, if a white ball is negative, adding it reduces the sum. So we should not take it
    #    unless we are forced to? But we are not forced to take a specific number, just <= k.
    #    So for a fixed k, we take the top min(k, M) white balls, but we can choose to take fewer.
    #    So we take the top j white balls where j = min(k, M) but only if they are positive?
    #    No, we take the top j white balls such that their sum is maximized.
    #    Since we can choose any j from 0 to min(k, M), we should take j such that sum of top j white balls is max.
    #    This is equivalent to taking all positive white balls, but limited by k.
    #    Let P_W be the list of positive white balls. Let count_pos_W = len(P_W).
    #    Then for a fixed k, the best j is min(k, count_pos_W).
    #    So for each k, sum = sum(B[:k]) + sum(W[:min(k, count_pos_W)]) where W is sorted descending.
    #    Wait, W is sorted descending. The top min(k, count_pos_W) elements are the largest positive ones.
    #    But what if k is large and there are negative white balls? We don't take them.
    #    So yes, for a fixed k, we take top k black balls and top min(k, count_pos_W) white balls.
    #    But wait, what if we take fewer black balls? We iterate k from 0 to N.
    #    Also, we can take 0 black balls and 0 white balls (sum=0).

    # Let's refine:
    # Sort B descending, W descending.
    # Precompute prefix sums for B and for W (only positive part? or all?).
    # Actually, for W, we only care about the positive ones. Let's separate W into positive and negative.
    # But since W is sorted descending, the positive ones come first.
    # So, let's compute prefix sums for B (all) and for W (all, but we will only use up to the positive ones).
    # Actually, we can just compute prefix sums for the entire sorted W, but when considering k,
    # we take min(k, M) elements from W, but we should only take the ones that are positive.
    # So, let's find the index where W becomes negative.
    # Let pos_W_count be the number of positive white balls.
    # Then for a given k, we take min(k, pos_W_count) white balls.
    # But wait, what if k is small, say k=1, and we have 5 positive white balls? We take 1.
    # What if k=10, and we have 5 positive white balls? We take 5.
    # So the number of white balls to take is min(k, pos_W_count).
    # But what if we take k black balls and j white balls where j < k?
    # The constraint is count(black) >= count(white). So if we take k black, we can take j white where 0 <= j <= k.
    # To maximize, we take j = min(k, pos_W_count).
    # So the algorithm:
    # 1. Sort B descending.
    # 2. Sort W descending.
    # 3. Compute prefix sums for B.
    # 4. Compute prefix sums for W, but note that we only want to take up to pos_W_count.
    #    Actually, we can just use the prefix sum of W up to min(k, pos_W_count).
    #    But we need to handle the case where we take 0 white balls.
    # 5. Iterate k from 0 to N.
    #    current_black_sum = prefix_B[k] (if k>0 else 0)
    #    num_white = min(k, pos_W_count)
    #    current_white_sum = prefix_W[num_white] (if num_white>0 else 0)
    #    total = current_black_sum + current_white_sum
    #    max_total = max(max_total, total)
    # 6. Also consider the case of taking 0 balls (sum=0).

    # However, there is a catch: what if taking some negative black balls allows us to take more positive white balls?
    # No, because adding a negative black ball reduces the sum and increases k, which might allow more white balls.
    # But since B is sorted descending, the black balls we take are the largest ones.
    # If we take a negative black ball, it's because we ran out of positive ones, and taking it allows us to take more white balls.
    # But the white balls we can take are limited by pos_W_count (the positive ones).
    # Once we have taken all positive white balls, adding more black balls (even negative) doesn't help because we can't take more positive white balls.
    # And taking negative white balls would reduce the sum.
    # So, we only consider k from 0 to N, and for each k, we take min(k, pos_W_count) white balls.
    # But wait, what if we take k black balls and j white balls where j < k and j > pos_W_count?
    # That would mean taking negative white balls, which is not optimal.
    # So the strategy holds.

    # Let's implement.

    B.sort(reverse=True)
    W.sort(reverse=True)

    # Compute prefix sums for B
    prefix_B = [0] * (N + 1)
    for i in range(N):
        prefix_B[i+1] = prefix_B[i] + B[i]

    # Find how many positive white balls there are
    pos_W_count = 0
    for x in W:
        if x > 0:
            pos_W_count += 1
        else:
            break

    # Compute prefix sums for W, but we only care up to pos_W_count
    # Actually, we can just use the prefix sum of the entire W, but we will only index up to pos_W_count.
    # But note: if we take j white balls, we take the first j of W (which are the largest).
    # Since W is sorted descending, the first pos_W_count are positive, and the rest are non-positive.
    # So we can compute prefix sums for W up to min(N, M) but we will only use up to pos_W_count.
    # However, to be safe, let's compute prefix sums for the entire W (up to M).
    prefix_W = [0] * (M + 1)
    for i in range(M):
        prefix_W[i+1] = prefix_W[i] + W[i]

    max_sum = 0  # At least 0 (choosing no balls)

    # Iterate k from 0 to N
    for k in range(N + 1):
        # Number of white balls to take
        num_white = min(k, pos_W_count)
        current_sum = prefix_B[k] + prefix_W[num_white]
        if current_sum > max_sum:
            max_sum = current_sum

    print(max_sum)

if __name__ == '__main__':
    solve()
