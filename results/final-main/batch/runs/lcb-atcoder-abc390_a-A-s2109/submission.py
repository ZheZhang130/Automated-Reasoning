import sys

def solve():
    # Read input from stdin
    line = sys.stdin.read().strip()
    parts = line.split()
    if not parts:
        return
    A = list(map(int, parts))
    
    # Target sorted array
    target = [1, 2, 3, 4, 5]
    
    # Try swapping every adjacent pair exactly once
    for i in range(4):  # indices 0 to 3 (swapping i and i+1)
        # Create a copy and swap
        B = A[:]
        B[i], B[i+1] = B[i+1], B[i]
        
        # Check if sorted
        if B == target:
            print("Yes")
            return
    
    # If no single swap works
    print("No")

if __name__ == "__main__":
    solve()
