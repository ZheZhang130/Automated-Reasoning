import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    A = [int(x) for x in input_data[1:]]
    
    if N == 0:
        print("Yes")
        return
    
    # Check if it's a geometric progression
    # For a geometric progression, A[i] / A[i-1] should be constant for all i
    # We need to handle floating point carefully or use cross-multiplication
    
    # First term
    first = A[0]
    
    # Calculate the ratio as a fraction to avoid floating point issues
    # ratio = A[1] / A[0]
    # We'll check if A[i] * A[0] == A[i-1] * A[1] for all i >= 2
    
    if N == 1:
        print("Yes")
        return
    
    # Check if A[1] / A[0] == A[2] / A[1] == ...
    # Using cross multiplication: A[i] * A[0] == A[i-1] * A[1] for all i >= 2
    
    # Actually, we need to check: A[i] / A[i-1] == A[i-1] / A[i-2] for all i >= 2
    # Which means: A[i] * A[i-2] == A[i-1] * A[i-1]
    
    # But a simpler approach: check if A[i] * A[0] == A[i-1] * A[1] for all i >= 1
    # This ensures A[i]/A[i-1] == A[1]/A[0]
    
    for i in range(1, N):
        if A[i] * A[0] != A[i-1] * A[1]:
            print("No")
            return
    
    print("Yes")

if __name__ == "__main__":
    solve()
