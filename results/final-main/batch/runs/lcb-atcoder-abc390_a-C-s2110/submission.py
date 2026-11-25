import sys

def solve():
    # Read input from stdin
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        parts = line.split()
        if len(parts) != 5:
            return
        A = list(map(int, parts))
    except ValueError:
        return

    target = [1, 2, 3, 4, 5]
    
    # Try swapping each adjacent pair exactly once
    # There are 4 adjacent pairs: (0,1), (1,2), (2,3), (3,4)
    for i in range(4):
        # Create a copy of A
        B = A[:]
        # Swap adjacent elements at i and i+1
        B[i], B[i+1] = B[i+1], B[i]
        # Check if sorted
        if B == target:
            print("Yes")
            return
    
    # If no swap leads to sorted array
    print("No")

if __name__ == "__main__":
    solve()
