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

    # Sort both arrays in descending order to pick best values first
    B.sort(reverse=True)
    W.sort(reverse=True)

    # We need to choose k black balls and k white balls for some k >= 0,
    # plus possibly some extra black balls (since black count must be >= white count).
    # Strategy:
    # 1. Consider taking k black balls and k white balls for k from 0 to min(N, M).
    #    For each k, we take the top k from B and top k from W.
    #    Then we can optionally add more black balls (from the remaining B) if they are positive.
    # 2. The maximum sum is the max over all k of (sum of top k B + sum of top k W + sum of positive remaining B).

    # Precompute prefix sums for B and W
    B_prefix = [0] * (N + 1)
    for i in range(N):
        B_prefix[i + 1] = B_prefix[i] + B[i]

    W_prefix = [0] * (M + 1)
    for i in range(M):
        W_prefix[i + 1] = W_prefix[i] + W[i]

    # Precompute suffix sums of positive values for B (from index k to N-1)
    # We want sum of B[i] for i from k to N-1 where B[i] > 0
    # Let's compute total sum of positive B from index k onwards
    # We can do this by precomputing suffix sums of positive values
    B_suffix_positive = [0] * (N + 1)
    for i in range(N - 1, -1, -1):
        if B[i] > 0:
            B_suffix_positive[i] = B_suffix_positive[i + 1] + B[i]
        else:
            B_suffix_positive[i] = B_suffix_positive[i + 1]

    max_total = 0

    # Try all possible k from 0 to min(N, M)
    limit = min(N, M)
    for k in range(limit + 1):
        current_sum = B_prefix[k] + W_prefix[k]
        # Add positive remaining black balls
        current_sum += B_suffix_positive[k]
        if current_sum > max_total:
            max_total = current_sum

    print(max_total)

if __name__ == "__main__":
    solve()
