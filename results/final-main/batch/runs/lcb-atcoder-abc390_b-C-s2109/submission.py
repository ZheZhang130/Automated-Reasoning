import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    n = int(input_data[0])
    a = [int(x) for x in input_data[1:]]
    
    if n == 0 or n == 1:
        print("Yes")
        return
    
    # For geometric progression, A[i] * A[1] == A[i-1] * A[0] for all i >= 2
    # This avoids floating point issues
    first = a[0]
    second = a[1]
    
    for i in range(2, n):
        if a[i] * first != a[i-1] * second:
            print("No")
            return
    
    print("Yes")

if __name__ == "__main__":
    solve()
