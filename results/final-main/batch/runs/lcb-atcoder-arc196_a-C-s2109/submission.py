import sys
import heapq

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    N = int(data[0])
    A = list(map(int, data[1:]))

    def get_even_prefix_scores(arr):
        # Returns list of scores for even-length prefixes: index i corresponds to prefix of length i
        # We'll compute for lengths 0, 2, 4, ...
        lower = []  # max-heap (store negatives)
        upper = []  # min-heap
        lower_sum = 0
        upper_sum = 0
        scores = [0] * (len(arr) + 1)
        for i, x in enumerate(arr):
            if not lower or x <= -lower[0]:
                heapq.heappush(lower, -x)
                lower_sum += x
            else:
                heapq.heappush(upper, x)
                upper_sum += x
            # Rebalance: lower should have same size as upper or one more
            if len(lower) > len(upper) + 1:
                moved = -heapq.heappop(lower)
                heapq.heappush(upper, moved)
                lower_sum -= moved
                upper_sum += moved
            elif len(upper) > len(lower):
                moved = heapq.heappop(upper)
                heapq.heappush(lower, -moved)
                lower_sum += moved
                upper_sum -= moved
            length = i + 1
            if length % 2 == 0:
                scores[length] = upper_sum - lower_sum
            else:
                scores[length] = 0
        return scores

    if N % 2 == 0:
        scores = get_even_prefix_scores(A)
        print(scores[N])
    else:
        # For odd N, we need to consider each odd index as the survivor
        # The survivor must be at an odd 1-based index (0-based even index)
        # We compute prefix scores for even-length prefixes and suffix scores for even-length suffixes
        # Then for each odd index i (0-based), total = prefix[i-1] + suffix[i+1]
        # But note: the problem says the survivor must have an odd 1-based index, meaning 0-based even index.
        # So we consider survivors at indices 0, 2, 4, ... (0-based)
        # For a survivor at index i (0-based), the left segment is A[0:i] (length i) and right segment is A[i+1:N] (length N-i-1)
        # Both segments must be even length to be completely deleted.
        # So i must be even (0-based) so that left segment length i is even, and N-i-1 must be even.
        # Since N is odd, N-i-1 is even iff i is even.
        # So we only consider even i (0-based).
        
        prefix_scores = get_even_prefix_scores(A)
        # For suffixes, we reverse the array and compute even prefix scores, then map back
        reversed_A = A[::-1]
        suffix_scores = get_even_prefix_scores(reversed_A)
        # suffix_scores[k] is the score for the suffix of length k (which is the first k elements of reversed_A)
        # The suffix starting at index i (0-based) has length N - 1 - i
        # So suffix_scores[N - 1 - i] is the score for the suffix starting at i
        
        best = 0
        for i in range(0, N, 2):  # i is even (0-based)
            left_len = i
            right_len = N - 1 - i
            left_score = prefix_scores[left_len]
            right_score = suffix_scores[right_len]
            total = left_score + right_score
            if total > best:
                best = total
        print(best)

if __name__ == "__main__":
    solve()
