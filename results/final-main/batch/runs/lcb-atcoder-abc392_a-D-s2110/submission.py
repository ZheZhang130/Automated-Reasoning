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
        a1, a2, a3 = map(int, parts)
    except ValueError:
        return

    # Check all permutations: (a1, a2, a3), (a1, a3, a2), (a2, a1, a3), (a2, a3, a1), (a3, a1, a2), (a3, a2, a1)
    # We need to check if any permutation (x, y, z) satisfies x * y == z
    values = [a1, a2, a3]
    
    # Generate all permutations
    from itertools import permutations
    for p in permutations(values):
        if p[0] * p[1] == p[2]:
            print("Yes")
            return
    
    print("No")

if __name__ == "__main__":
    solve()
