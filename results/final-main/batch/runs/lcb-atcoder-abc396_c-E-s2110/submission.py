import sys

def solve() -> None:
    input_data = sys.stdin.read().split()
    iterator = iter(input_data)
    
    N = int(next(iterator))
    M = int(next(iterator))
    
    B = []
    for _ in range(N):
        B.append(int(next(iterator)))
    
    W = []
    for _ in range(M):
        W.append(int(next(iterator)))
    
    # Sort both arrays in descending order
    B.sort(reverse=True)
    W.sort(reverse=True)
    
    # Calculate suffix sums of positive black balls
    # suffix_positive_B[i] = sum of positive black balls from B[i] to B[N-1]
    suffix_positive_B = [0] * (N + 1)
    for i in range(N - 1, -1, -1):
        suffix_positive_B[i] = suffix_positive_B[i + 1] + (B[i] if B[i] > 0 else 0)
    
    max_sum = 0
    
    # k=0: choose 0 white balls, 0 black balls initially, then add all positive black balls
    total = 0 + 0 + suffix_positive_B[0]
    max_sum = max(max_sum, total)
    
    # k from 1 to min(N, M): choose k white balls and k black balls
    for k in range(1, min(N, M) + 1):
        current_white_sum = sum(W[:k])
        current_black_sum = sum(B[:k])
        total = current_white_sum + current_black_sum + suffix_positive_B[k]
        max_sum = max(max_sum, total)
    
    print(max_sum)

if __name__ == "__main__":
    solve()
