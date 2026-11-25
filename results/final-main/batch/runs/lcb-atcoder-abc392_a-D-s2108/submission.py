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
        a = [int(x) for x in parts]
    except ValueError:
        return

    # Check all permutations: a[0]*a[1] == a[2], a[0]*a[2] == a[1], a[1]*a[2] == a[0]
    if a[0] * a[1] == a[2]:
        print("Yes")
    elif a[0] * a[2] == a[1]:
        print("Yes")
    elif a[1] * a[2] == a[0]:
        print("Yes")
    else:
        print("No")

if __name__ == "__main__":
    solve()
