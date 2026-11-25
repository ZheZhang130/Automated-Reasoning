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
    
    # Calculate the common ratio as a fraction to avoid floating point issues
    # ratio = a[1] / a[0]
    # We check if a[i] / a[i-1] == a[1] / a[0] for all i
    # This is equivalent to a[i] * a[0] == a[i-1] * a[1]
    
    a0 = a[0]
    a1 = a[1]
    
    # Check for all consecutive pairs
    for i in range(2, n):
        if a[i] * a0 != a[i-1] * a1:
            print("No")
            return
    
    print("Yes")

if __name__ == "__main__":
    solve()
