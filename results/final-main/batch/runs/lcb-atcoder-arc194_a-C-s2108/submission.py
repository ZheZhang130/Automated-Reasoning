import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    N = int(next(iterator))
    A = [int(next(iterator)) for _ in range(N)]
    
    # F[i] represents the maximum sum achievable after processing i elements
    # Base cases:
    # F[0] = 0 (empty stack, sum 0)
    # F[1] = A[0] (must append first element)
    
    # Recurrence:
    # For i >= 2:
    # Option 1: Append A[i-1] to the best stack from i-1 operations -> F[i-1] + A[i-1]
    # Option 2: The last operation was a delete, meaning we effectively skipped A[i-1] 
    #            and the stack is the same as after i-2 operations -> F[i-2]
    # We take the max of these two options.
    
    if N == 0:
        print(0)
        return
    
    if N == 1:
        print(A[0])
        return
    
    # We only need the last two values to compute the next one
    prev2 = 0  # F[0]
    prev1 = A[0]  # F[1]
    
    for i in range(2, N + 1):
        current = max(prev1 + A[i-1], prev2)
        prev2 = prev1
        prev1 = current
    
    print(prev1)

if __name__ == "__main__":
    solve()
