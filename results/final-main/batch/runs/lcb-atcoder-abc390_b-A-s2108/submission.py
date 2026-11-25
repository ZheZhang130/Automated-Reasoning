import sys

def main():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    n = int(input_data[0])
    a = [int(x) for x in input_data[1:n+1]]
    
    if n == 1:
        print("Yes")
        return
    
    # Check if it's a geometric progression
    # For a geometric progression, A[i] / A[i-1] should be constant
    # We use cross-multiplication to avoid floating point issues: A[i] * A[i-2] == A[i-1]^2
    # But we need to handle the first ratio separately
    
    # Calculate the first ratio as a fraction
    # ratio = A[1] / A[0]
    # For subsequent terms: A[i] = A[i-1] * ratio
    # So A[i] * A[0] = A[i-1] * A[1]
    
    for i in range(2, n):
        if a[i] * a[0] != a[i-1] * a[1]:
            print("No")
            return
    
    print("Yes")

if __name__ == "__main__":
    main()
