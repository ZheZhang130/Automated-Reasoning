import sys

def solve():
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
    
    # Sort both lists in descending order
    B.sort(reverse=True)
    W.sort(reverse=True)
    
    # Prefix sums for black balls
    # We'll compute them on the fly during iteration
    
    # Prefix sums for white balls
    # We'll compute them on the fly during iteration
    
    # Current sum of black balls chosen
    current_black_sum = 0
    
    # Current sum of white balls chosen (for the maximum feasible white count)
    current_white_sum = 0
    
    # Best white sum seen so far for the current k
    best_white_sum = 0
    
    # Best total answer
    best_answer = 0
    
    # Iterate k from 1 to N (number of black balls chosen)
    for k in range(1, N + 1):
        current_black_sum += B[k-1]
        
        # Update best white sum if we can choose k white balls
        if k <= M:
            current_white_sum += W[k-1]
            if current_white_sum > best_white_sum:
                best_white_sum = current_white_sum
        
        # Total sum for this k
        total = current_black_sum + best_white_sum
        if total > best_answer:
            best_answer = total
    
    print(best_answer)

if __name__ == "__main__":
    solve()
