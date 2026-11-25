import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    n = int(input_data[0])
    a = [int(x) for x in input_data[1:n+1]]
    
    if n == 1:
        print("Yes")
        return
    
    # Calculate the ratio from the first two terms
    # Since all A_i are positive integers, we can use cross-multiplication to avoid floating point issues
    # For a geometric progression: A[i] / A[i-1] = A[i-1] / A[i-2]
    # This is equivalent to: A[i] * A[i-2] == A[i-1] * A[i-1]
    
    # First, calculate the ratio as a fraction (numerator, denominator)
    # ratio = a[1] / a[0]
    num = a[1]
    den = a[0]
    
    # Check if this ratio holds for all consecutive pairs
    for i in range(2, n):
        # Check if a[i] / a[i-1] == num / den
        # Cross-multiply: a[i] * den == a[i-1] * num
        if a[i] * den != a[i-1] * num:
            print("No")
            return
    
    print("Yes")

if __name__ == "__main__":
    solve()
