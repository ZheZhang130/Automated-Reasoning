import sys

def solve():
    # Read input from stdin
    line = sys.stdin.read().strip()
    parts = line.split()
    A = list(map(int, parts))
    
    # Target sorted sequence
    target = [1, 2, 3, 4, 5]
    
    # Try swapping each adjacent pair exactly once
    for i in range(4):  # indices 0 to 3 (swapping i and i+1)
        # Create a new list with the swap
        new_A = A.copy()
        new_A[i], new_A[i+1] = new_A[i+1], new_A[i]
        
        # Check if it matches the target
        if new_A == target:
            print("Yes")
            return
    
    # If no single adjacent swap works
    print("No")

if __name__ == "__main__":
    solve()
