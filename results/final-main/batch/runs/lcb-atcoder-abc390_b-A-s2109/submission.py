import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    A = list(map(int, input_data[1:N+1]))
    
    if N == 1:
        print("Yes")
        return
    
    # Check if it's a geometric progression
    # For a geometric progression, A[i] / A[i-1] should be constant for all i
    # We need to handle the case where the ratio might not be an integer
    
    # Calculate the ratio from the first two elements
    # Since A[i] are positive integers, we can use cross-multiplication to avoid floating point issues
    # A[i] * A[i-2] == A[i-1] * A[i-1] for all i >= 2
    
    # First, check if the first two elements are equal
    if A[0] == A[1]:
        # Ratio is 1, all elements must be equal
        if all(x == A[0] for x in A):
            print("Yes")
        else:
            print("No")
        return
    
    # Calculate the ratio as a fraction
    # We'll use cross-multiplication: A[i] * A[i-2] == A[i-1] * A[i-1]
    # Actually, for geometric progression: A[i] / A[i-1] = r
    # So A[i] * A[i-2] = A[i-1] * A[i-1] is not correct
    # Correct: A[i] * A[i-2] = A[i-1]^2 is for geometric mean, but we need constant ratio
    
    # Let's use: A[i] * A[i-2] == A[i-1] * A[i-1] is wrong
    # Correct condition: A[i] / A[i-1] = A[i-1] / A[i-2]
    # Which means: A[i] * A[i-2] == A[i-1] * A[i-1] is still wrong
    
    # Actually: A[i] / A[i-1] = r, so A[i] = A[i-1] * r
    # For integer arithmetic: A[i] * A[i-2] == A[i-1] * A[i-1] is not the right check
    
    # The correct check is: A[i] * A[i-2] == A[i-1] * A[i-1] is for geometric mean
    # For geometric progression: A[i] / A[i-1] = A[i-1] / A[i-2]
    # Cross multiply: A[i] * A[i-2] == A[i-1] * A[i-1] is wrong
    
    # Let me recalculate:
    # A[1]/A[0] = A[2]/A[1] = ... = r
    # So A[1]*A[1] = A[0]*A[2], A[2]*A[2] = A[1]*A[3], etc.
    # General: A[i]^2 = A[i-1]*A[i+1]
    
    # Check this condition for all i from 1 to N-2
    is_gp = True
    for i in range(1, N-1):
        if A[i] * A[i] != A[i-1] * A[i+1]:
            is_gp = False
            break
    
    if is_gp:
        print("Yes")
    else:
        print("No")

if __name__ == "__main__":
    solve()
