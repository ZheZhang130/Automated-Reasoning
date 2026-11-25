import sys
import heapq

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    A = [int(x) for x in input_data[1:]]

    def get_best_even_scores(arr):
        lower = []  # max-heap (store negated values)
        upper = []  # min-heap
        sum_lower = 0
        sum_upper = 0
        scores = []
        for x in arr:
            if not lower or x <= -lower[0]:
                heapq.heappush(lower, -x)
                sum_lower += x
            else:
                heapq.heappush(upper, x)
                sum_upper += x
            # Rebalance: lower should have same size as upper or one more
            if len(lower) > len(upper) + 1:
                moved = -heapq.heappop(lower)
                sum_lower -= moved
                heapq.heappush(upper, moved)
                sum_upper += moved
            elif len(upper) > len(lower):
                moved = heapq.heappop(upper)
                sum_upper -= moved
                heapq.heappush(lower, -moved)
                sum_lower += moved
            # Record score if even length
            total_len = len(lower) + len(upper)
            if total_len % 2 == 0:
                scores.append(sum_upper - sum_lower)
            else:
                scores.append(0)
        return scores

    if N % 2 == 0:
        scores = get_best_even_scores(A)
        print(scores[-1])
    else:
        prefix_scores = get_best_even_scores(A)
        suffix_scores = get_best_even_scores(A[::-1])
        
        max_total = 0
        for i in range(N):
            left_len = i
            right_len = N - 1 - i
            if left_len % 2 == 0 and right_len % 2 == 0:
                left_score = prefix_scores[left_len] if left_len <= len(prefix_scores) else 0
                right_score = suffix_scores[right_len] if right_len <= len(suffix_scores) else 0
                total = left_score + right_score
                if total > max_total:
                    max_total = total
        print(max_total)

if __name__ == "__main__":
    solve()
