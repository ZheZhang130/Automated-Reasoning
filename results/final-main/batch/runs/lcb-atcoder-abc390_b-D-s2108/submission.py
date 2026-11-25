import sys

def main():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0])
    a = [int(x) for x in data[1:n+1]]
    
    if n == 1:
        print("Yes")
        return
    
    # For geometric progression: A[i] / A[i-1] = r (constant)
    # So A[i] / A[i-1] = A[i-1] / A[i-2]
    # Cross multiply: A[i] * A[i-2] = A[i-1] * A[i-1] is wrong
    # Correct: A[i] * A[i-2] = A[i-1] * A[i-1] is for geometric mean
    
    # Actually the correct check is: A[i] / A[i-1] = A[i-1] / A[i-2]
    # => A[i] * A[i-2] = A[i-1] * A[i-1] is wrong
    # => A[i] * A[i-2] = A[i-1] * A[i-1] is wrong
    
    # Let me recalculate: A[i] / A[i-1] = A[i-1] / A[i-2]
    # Cross multiply: A[i] * A[i-2] = A[i-1] * A[i-1] is wrong
    # Cross multiply: A[i] * A[i-2] = A[i-1] * A[i-1] is wrong
    
    # Correct: A[i] * A[i-2] = A[i-1] * A[i-1] is for geometric mean
    # For ratio equality: A[i] / A[i-1] = A[i-1] / A[i-2]
    # => A[i] * A[i-2] = A[i-1] * A[i-1] is wrong
    
    # Let me just compute the ratio as a fraction and compare
    # First ratio: r = A[1] / A[0]
    # Then check if A[i] / A[i-1] == r for all i
    
    # To avoid float, use cross-multiplication:
    # A[i] / A[i-1] = A[1] / A[0]
    # => A[i] * A[0] = A[i-1] * A[1]
    
    first = a[0]
    second = a[1]
    
    for i in range(2, n):
        if a[i] * first != a[i-1] * second:
            print("No")
            return
    
    print("Yes")

if __name__ == "__main__":
    main()
