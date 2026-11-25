import sys

def solve():
    input = sys.stdin.read
    data = input().split()
    iterator = iter(data)
    
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
    
    # Prefix sums for black balls
    # We'll compute them on the fly
    
    # Prefix sums for white balls
    # We'll compute them on the fly
    
    # Current sum of black balls chosen
    current_black_sum = 0
    
    # Current sum of white balls chosen (we can choose up to k white balls)
    # We maintain the best white prefix sum for each k
    
    # Best white prefix sum for each k (from 0 to min(k, M))
    # We'll maintain a running maximum
    
    # Initialize
    best_white_sum = 0  # For k=0, we can choose 0 white balls with sum 0
    
    # We need to track the best white prefix sum for each k
    # Since we iterate k from 0 to N, we can maintain the best white prefix sum
    
    # Actually, we need to be careful: for a given k, we can choose any number of white balls from 0 to min(k, M)
    # So we need to maintain the maximum white prefix sum for each possible count
    
    # Let's maintain:
    # current_white_sum: sum of white balls chosen so far (for the current k)
    # best_white_sum: maximum white prefix sum seen so far (for counts 0 to min(k, M))
    
    current_white_sum = 0
    best_white_sum = 0
    
    # We also need to consider the case where we choose 0 black balls and 0 white balls (sum = 0)
    # This is already covered by our initialization
    
    ans = 0
    
    # Iterate over the number of black balls chosen (from 0 to N)
    # But we need to handle k=0 separately
    
    # For k=0: we choose 0 black balls, and 0 white balls (since we can't choose any white balls if k=0)
    # Actually, the constraint is: number of black balls >= number of white balls
    # So if we choose 0 black balls, we must choose 0 white balls
    
    # Let's iterate k from 0 to N
    # For k=0: current_black_sum = 0, current_white_sum = 0, best_white_sum = 0
    # For k > 0: we add B[k-1] to current_black_sum, and we can add W[k-1] to current_white_sum if k <= M
    
    # But we need to maintain the best white prefix sum for each k
    
    # Actually, the approach is:
    # For each k from 0 to N:
    #   current_black_sum = sum of first k black balls (sorted descending)
    #   We can choose any number of white balls from 0 to min(k, M)
    #   So we need the maximum white prefix sum for counts 0 to min(k, M)
    #   We can maintain this as we iterate
    
    # Let's do it step by step
    
    # Initialize for k=0
    current_black_sum = 0
    current_white_sum = 0
    best_white_sum = 0
    ans = 0
    
    # Now iterate k from 1 to N
    for k in range(1, N + 1):
        # Add the k-th black ball (0-indexed, so B[k-1])
        current_black_sum += B[k-1]
        
        # Update the white prefix sum if we can add another white ball
        if k <= M:
            current_white_sum += W[k-1]
            # The best white sum for this k is max of all previous best_white_sum and current_white_sum
            # But actually, we need to maintain the best white sum for each possible count
            # Since we can choose any number of white balls from 0 to min(k, M),
            # the best white sum for this k is the maximum of all white prefix sums from 0 to min(k, M)
            # We can maintain this by taking max with the previous best_white_sum and the new current_white_sum
            best_white_sum = max(best_white_sum, current_white_sum)
        else:
            # We can't add more white balls, so the best white sum remains the same
            # But we need to make sure we don't decrease it
            # Actually, best_white_sum should remain the maximum seen so far
            pass
        
        # Calculate the total sum for this k
        total = current_black_sum + best_white_sum
        ans = max(ans, total)
    
    print(ans)

if __name__ == "__main__":
    solve()
