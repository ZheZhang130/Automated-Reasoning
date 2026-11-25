import sys
from collections import Counter

def solve():
    input_data = sys.stdin.read().split()
    N = int(input_data[0])
    M = int(input_data[1])
    S = input_data[2]
    T = input_data[3]

    # Count frequency of each digit in T
    t_counts = Counter(T)
    
    # We need to place the largest available digits from T into S
    # Strategy: For each position in S, we want to put the largest possible digit
    # that we still have in T. But we must use all digits in T exactly once.
    # 
    # Key insight: We can choose ANY position i for each k.
    # So we can think of it as: we have M operations, each with a digit from T.
    # We want to place these M digits into M positions of S (out of N positions).
    # The remaining N-M positions will keep their original values.
    #
    # To maximize the result:
    # 1. We should use our "best" digits (largest ones) in the most significant positions.
    # 2. We should keep the original digits in positions where they are better than what we can provide.
    #
    # Algorithm:
    # - Sort T's digits in descending order.
    # - We have N positions. We will fill M of them with digits from T.
    # - The best strategy: 
    #   * Consider positions from left to right (most significant first).
    #   * At each position, decide whether to replace it with a digit from T or keep the original.
    #   * We should replace if the best available digit from T is greater than the current digit.
    #   * But we must save our best digits for earlier positions.
    #
    # Better approach:
    # - We have a multiset of digits from T.
    # - We want to assign these to M positions to maximize the result.
    # - Greedy from left to right:
    #   * Maintain a sorted list (descending) of available digits from T.
    #   * For position i from 0 to N-1:
    #     * If i < M (we can replace this position):
    #       * Compare the largest available digit from T with S[i].
    #       * If largest_T > S[i], use largest_T at position i, remove it from T.
    #       * Else, keep S[i] at position i.
    #     * If i >= M, we must keep S[i] (no more operations left).
    #
    # Wait, this is not quite right. We can choose ANY position for each operation.
    # So we should think of it as: we have M digits to place, and we want to place them
    # in the positions where they give the most benefit.
    #
    # Correct greedy strategy:
    # - Sort T's digits in descending order.
    # - We have N positions. We'll fill min(N, M) positions with digits from T.
    # - Actually, we fill exactly M positions (if N >= M) or all N positions (if N < M).
    # - But we can choose which positions to fill.
    # - To maximize: fill positions from left to right with the largest available digits
    #   that are greater than the current digit at that position.
    #
    # Even better: 
    # - We have M digits to place. We should place them in the M positions (from left)
    #   where they give the most benefit.
    # - Sort T descending.
    # - For each position i from 0 to min(N, M)-1:
    #   * We can choose to replace S[i] with T[i] (after sorting T descending).
    #   * But we might want to skip some positions and use later ones.
    # - Actually, the optimal strategy is:
    #   * Sort T descending.
    #   * For positions 0 to min(N, M)-1, we compare T[i] with S[i].
    #   * If T[i] > S[i], we replace S[i] with T[i].
    #   * But we need to be careful: we might want to save a larger digit for an earlier position.
    #
    # Let me reconsider:
    # We have M operations, each with a digit from T. We can choose any position for each.
    # To maximize the result:
    # - We should use our largest digits in the most significant positions.
    # - For each position from left to right, we decide whether to replace it.
    # - We should replace position i with the largest available digit from T that is > S[i].
    # - But we need to be greedy: use the largest possible digit at each position where it helps.
    #
    # Final algorithm:
    # 1. Sort T in descending order.
    # 2. For i from 0 to min(N, M)-1:
    #    - If T[i] > S[i], replace S[i] with T[i].
    #    - Else, keep S[i].
    # 3. For i from min(N, M) to N-1, keep S[i].
    #
    # Wait, this is still not quite right. We might have T[i] < S[i] but a later T[j] > S[i].
    # But since T is sorted descending, T[i] >= T[j] for i < j.
    # So if T[i] <= S[i], then all T[j] for j > i are also <= S[i].
    # So the greedy strategy works!
    
    # Sort T descending
    T_sorted = sorted(T, reverse=True)
    
    # Build result
    result = list(S)
    n_ops = min(N, M)
    
    for i in range(n_ops):
        if T_sorted[i] > result[i]:
            result[i] = T_sorted[i]
    
    print(''.join(result))

solve()
