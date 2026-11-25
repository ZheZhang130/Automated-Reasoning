import sys

def solve():
    # Read input
    line = sys.stdin.read().strip()
    parts = line.split()
    A = list(map(int, parts))
    
    # Target sorted sequence
    target = [1, 2, 3, 4, 5]
    
    # Check if already sorted
    if A == target:
        # Already sorted, but we must perform exactly one swap
        # Any swap will break the sorted order, so we cannot sort it with exactly one operation
        print("No")
        return
    
    # Try swapping each adjacent pair
    for i in range(4):  # indices 0 to 3 (swapping i and i+1)
        # Create a new list with swapped elements
        new_A = A.copy()
        new_A[i], new_A[i+1] = new_A[i+1], new_A[i]
        
        # Check if it matches target
        if new_A == target:
            print("Yes")
            return
    
    # If no single swap works
    print("No")

if __name__ == "__main__":
    solve()
