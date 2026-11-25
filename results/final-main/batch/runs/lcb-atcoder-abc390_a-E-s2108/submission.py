def solve():
    import sys
    data = sys.stdin.read().strip().split()
    A = [int(x) for x in data]
    target = [1, 2, 3, 4, 5]
    # Try swapping each adjacent pair exactly once
    for i in range(4):
        # Swap A[i] and A[i+1]
        B = A[:]
        B[i], B[i+1] = B[i+1], B[i]
        if B == target:
            print("Yes")
            return
    print("No")

if __name__ == "__main__":
    solve()
