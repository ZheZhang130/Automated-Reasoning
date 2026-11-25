import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    try:
        N = int(next(iterator))
        A = []
        for _ in range(N):
            A.append(int(next(iterator)))
    except StopIteration:
        return

    if N == 0:
        print(0)
        return

    # F[i] represents the maximum sum achievable after processing i elements
    # Base cases:
    # F[0] = 0 (empty stack, sum 0)
    # F[1] = A[0] (must append first element)
    
    # For i >= 2:
    # Option 1: Append A[i-1] (0-indexed) to the best stack from F[i-1]
    # Option 2: The last operation is a delete, meaning we effectively skip A[i-1] 
    #            and take the best from F[i-2] (since we must have at least 2 ops to delete)
    
    # However, we need to be careful: the recurrence F[i] = max(F[i-1] + A[i-1], F[i-2])
    # assumes that if we choose F[i-2], we can always form a valid sequence ending with a delete.
    # This is true because F[i-2] is a valid state (non-empty or empty), and we can always
    # append then delete the last element (which might be the one we just appended or not,
    # but the net effect is we don't include A[i-1] in the final sum).
    
    # Let's implement the DP:
    # dp[i] = max sum after i operations
    
    # We only need the last two values.
    
    prev2 = 0  # F[0]
    prev1 = A[0]  # F[1]
    
    for i in range(2, N + 1):
        current_val = A[i-1]
        # Option 1: Append current_val to the best stack from prev1
        option1 = prev1 + current_val
        # Option 2: Don't include current_val, take best from prev2
        option2 = prev2
        
        current = max(option1, option2)
        prev2 = prev1
        prev1 = current
    
    print(prev1)

if __name__ == "__main__":
    solve()
