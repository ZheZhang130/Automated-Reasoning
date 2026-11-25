import sys

def solve():
    data = sys.stdin.read().strip().split()
    if len(data) != 3:
        return
    a = [int(x) for x in data]
    # Check all permutations: (a[0], a[1], a[2]), (a[0], a[2], a[1]), (a[1], a[0], a[2]), etc.
    # We need a[i] * a[j] == a[k] where i, j, k are distinct indices.
    # Since there are only 3 elements, we can just check all 6 permutations.
    from itertools import permutations
    for p in permutations(a):
        if p[0] * p[1] == p[2]:
            print("Yes")
            return
    print("No")

if __name__ == "__main__":
    solve()
