import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    n = int(input_data[0])
    a = [int(x) for x in input_data[1:]]
    
    if n == 0:
        print("Yes")
        return
    
    if n == 1:
        print("Yes")
        return
    
    # For geometric progression, A[i] / A[i-1] must be constant for all i
    # Since all terms are positive, we can use cross-multiplication to avoid floating point issues
    # A[i] * A[i-2] == A[i-1] * A[i-1] is not the right check
    # We need: A[i] / A[i-1] == A[i-1] / A[i-2] for all i from 2 to n-1
    # Which is equivalent to: A[i] * A[i-2] == A[i-1] * A[i-1]
    # Wait, that's not right either.
    # The correct condition is: A[i] / A[i-1] == A[i-1] / A[i-2]
    # Cross multiply: A[i] * A[i-2] == A[i-1] * A[i-1]
    # No, that's still wrong. Let me re-derive.
    # We want A[i] / A[i-1] == A[i-1] / A[i-2]
    # Cross multiply: A[i] * A[i-2] == A[i-1] * A[i-1]
    # That's not right. Let's use the first two terms as reference.
    # Let r = A[1] / A[0] (using 0-indexed)
    # Then we need A[i] == A[0] * r^i for all i
    # Or equivalently, A[i] * A[0] == A[i-1] * A[1] for all i from 1 to n-1
    
    # Actually, the simplest approach:
    # Check if A[i] * A[0] == A[i-1] * A[1] for all i from 1 to n-1
    # This avoids floating point and handles fractional ratios correctly.
    
    a0 = a[0]
    a1 = a[1]
    
    for i in range(1, n):
        if a[i] * a0 != a[i-1] * a1:
            print("No")
            return
    
    print("Yes")

if __name__ == "__main__":
    solve()
