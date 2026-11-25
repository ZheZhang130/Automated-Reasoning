import sys

def solve():
    # Read input
    line = sys.stdin.read().strip()
    parts = line.split()
    if len(parts) != 5:
        return
    A = [int(x) for x in parts]
    
    # Check if already sorted
    if A == [1, 2, 3, 4, 5]:
        print("No")
        return
    
    # Try swapping each adjacent pair
    for i in range(4):
        # Create a new list with swapped elements
        new_A = A[:]
        new_A[i], new_A[i+1] = new_A[i+1], new_A[i]
        if new_A == [1, 2, 3, 4, 5]:
            print("Yes")
            return
    
    print("No")

if __name__ == "__main__":
    solve()
