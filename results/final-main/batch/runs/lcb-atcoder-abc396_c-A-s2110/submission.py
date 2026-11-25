import sys

def solve() -> None:
    input_data = sys.stdin.read().split()
    iterator = iter(input_data)
    
    N = int(next(iterator))
    M = int(next(iterator))
    
    B = [int(next(iterator)) for _ in range(N)]
    W = [int(next(iterator)) for _ in range(M)]
    
    # Sort both arrays in descending order
    B.sort(reverse=True)
    W.sort(reverse=True)
    
    # Compute suffix sums of positive B
    suffix_positive_B = [0] * (N + 1)
    for i in range(N - 1, -1, -1):
        suffix_positive_B[i] = suffix_positive_B[i + 1] + (B[i] if B[i] > 0 else 0)
    
    # Compute prefix sums for W
    W_prefix = [0] * (M + 1)
    for i in range(M):
        W_prefix[i + 1] = W_prefix[i] + W[i]
    
    max_sum = 0
    
    # k=0: choose 0 white balls, and all positive black balls
    total = suffix_positive_B[0]
    max_sum = max(max_sum, total)
    
    # k from 1 to min(M, N)
    for k in range(1, min(M, N) + 1):
        current_white_sum = W_prefix[k]
        current_black_sum = sum(B[:k])
        total = current_white_sum + current_black_sum + suffix_positive_B[k]
        max_sum = max(max_sum, total)
    
    # k from N+1 to M: we choose all N black balls and k white balls
    # But we can only choose up to N black balls, so for k > N, we choose all N black balls
    # and k white balls. But we must have black_count >= white_count, so we can't choose k > N white balls.
    # Wait, the constraint is black_count >= white_count.
    # So if we choose k white balls, we must choose at least k black balls.
    # But we only have N black balls. So k can be at most N.
    # So we only need to consider k from 0 to min(M, N).
    
    print(max_sum)

if __name__ == "__main__":
    solve()
