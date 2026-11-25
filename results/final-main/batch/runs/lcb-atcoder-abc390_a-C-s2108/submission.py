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
        A = [int(x) for x in parts]
    except ValueError:
        return

    target = [1, 2, 3, 4, 5]
    
    # Try all 4 possible adjacent swaps
    # Swap positions (0,1)
    A[0], A[1] = A[1], A[0]
    if A == target:
        print("Yes")
        return
    A[0], A[1] = A[1], A[0]  # Undo
    
    # Swap positions (1,2)
    A[1], A[2] = A[2], A[1]
    if A == target:
        print("Yes")
        return
    A[1], A[2] = A[2], A[1]  # Undo
    
    # Swap positions (2,3)
    A[2], A[3] = A[3], A[2]
    if A == target:
        print("Yes")
        return
    A[2], A[3] = A[3], A[2]  # Undo
    
    # Swap positions (3,4)
    A[3], A[4] = A[4], A[3]
    if A == target:
        print("Yes")
        return
    A[3], A[4] = A[4], A[3]  # Undo
    
    # If no swap works
    print("No")

if __name__ == "__main__":
    solve()
