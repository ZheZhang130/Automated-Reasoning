import sys

def solve():
    # Read input
    line = sys.stdin.read().strip()
    if not line:
        return
    A = list(map(int, line.split()))
    
    target = [1, 2, 3, 4, 5]
    
    # Try each adjacent swap
    for i in range(4):
        # Create a copy and swap adjacent elements
        B = A.copy()
        B[i], B[i+1] = B[i+1], B[i]
        
        # Check if sorted
        if B == target:
            print("Yes")
            return
    
    # If no swap works
    print("No")

if __name__ == "__main__":
    solve()
