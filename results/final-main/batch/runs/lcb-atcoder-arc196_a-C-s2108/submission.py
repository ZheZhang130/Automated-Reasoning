import sys
import heapq

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    N = int(next(iterator))
    A = [int(next(iterator)) for _ in range(N)]

    # We need to compute for each even-length prefix the score = sum(upper) - sum(lower)
    # where we maintain a max-heap for lower half and min-heap for upper half.
    # The heaps will be balanced such that len(lower) == len(upper) or len(lower) == len(upper) + 1.
    # For even length, len(lower) == len(upper).

    # We'll compute prefix scores for even lengths.
    # Similarly, we'll compute suffix scores for even lengths.

    # Prefix scan
    lower = []  # max-heap (store negative values)
    upper = []  # min-heap
    sum_lower = 0
    sum_upper = 0
    prefix_scores = {}  # length -> score

    for i in range(N):
        val = A[i]
        if not lower or val <= -lower[0]:
            heapq.heappush(lower, -val)
            sum_lower += val
        else:
            heapq.heappush(upper, val)
            sum_upper += val

        # Rebalance: we want len(lower) == len(upper) or len(lower) == len(upper) + 1
        # If len(lower) > len(upper) + 1, move max from lower to upper
        # If len(upper) > len(lower), move min from upper to lower
        while len(lower) > len(upper) + 1:
            moved = -heapq.heappop(lower)
            sum_lower -= moved
            heapq.heappush(upper, moved)
            sum_upper += moved
        while len(upper) > len(lower):
            moved = heapq.heappop(upper)
            sum_upper -= moved
            heapq.heappush(lower, -moved)
            sum_lower += moved

        length = len(lower) + len(upper)
        if length % 2 == 0:
            prefix_scores[length] = sum_upper - sum_lower

    # Suffix scan
    lower = []
    upper = []
    sum_lower = 0
    sum_upper = 0
    suffix_scores = {}  # length -> score

    for i in range(N - 1, -1, -1):
        val = A[i]
        if not lower or val <= -lower[0]:
            heapq.heappush(lower, -val)
            sum_lower += val
        else:
            heapq.heappush(upper, val)
            sum_upper += val

        while len(lower) > len(upper) + 1:
            moved = -heapq.heappop(lower)
            sum_lower -= moved
            heapq.heappush(upper, moved)
            sum_upper += moved
        while len(upper) > len(lower):
            moved = heapq.heappop(upper)
            sum_upper -= moved
            heapq.heappush(lower, -moved)
            sum_lower += moved

        length = len(lower) + len(upper)
        if length % 2 == 0:
            suffix_scores[length] = sum_upper - sum_lower

    # Now, for each odd index i (1-based), the survivor is A[i-1] (0-based index i-1)
    # The left segment is A[0:i-1] (length i-1) and right segment is A[i:N] (length N-i)
    # We need both lengths to be even. So i-1 must be even => i is odd.
    # And N-i must be even => N and i have same parity. Since i is odd, N must be odd.
    # If N is even, we can only have one segment (the whole array) if we consider the survivor as not existing?
    # Actually, if N is even, we delete everything, so there is no survivor. The answer is prefix_scores[N].
    # If N is odd, we must have a survivor. The survivor must be at an odd 1-based index.
    # So for each odd i from 1 to N, left length = i-1 (even), right length = N-i (even).
    # We take max(prefix_scores[i-1] + suffix_scores[N-i]).

    if N % 2 == 0:
        print(prefix_scores[N])
    else:
        max_score = 0
        # i is 1-based index of survivor
        for i in range(1, N + 1, 2):  # i = 1, 3, 5, ...
            left_len = i - 1
            right_len = N - i
            # Ensure we have scores for these lengths (they should, but let's be safe)
            if left_len in prefix_scores and right_len in suffix_scores:
                score = prefix_scores[left_len] + suffix_scores[right_len]
                if score > max_score:
                    max_score = score
            else:
                # This shouldn't happen with correct logic, but handle it
                score = 0
                if left_len in prefix_scores:
                    score += prefix_scores[left_len]
                if right_len in suffix_scores:
                    score += suffix_scores[right_len]
                if score > max_score:
                    max_score = score
        print(max_score)

if __name__ == "__main__":
    solve()
