import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    n = int(input_data[0])
    a = [int(x) for x in input_data[1:]]
    
    if n == 1:
        print("Yes")
        return
    
    # For a geometric progression, A[i] * A[0] == A[i-1] * A[1] for all i >= 2
    # This avoids floating point issues
    a0 = a[0]
    a1 = a[1]
    
    for i in range(2, n):
        if a[i] * a0 != a[i-1] * a1:
            print("No")
            return
    
    print("Yes")

if __name__ == "__main__":
    solve()
