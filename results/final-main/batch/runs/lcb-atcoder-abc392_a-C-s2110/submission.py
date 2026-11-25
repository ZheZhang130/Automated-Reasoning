import sys

def solve():
    # Read three integers from standard input
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        parts = line.split()
        if len(parts) != 3:
            return
        a, b, c = map(int, parts)
    except ValueError:
        return

    # Sort the three values
    nums = sorted([a, b, c])
    x, y, z = nums[0], nums[1], nums[2]

    # Check if x * y == z
    if x * y == z:
        print("Yes")
    else:
        print("No")

if __name__ == "__main__":
    solve()
