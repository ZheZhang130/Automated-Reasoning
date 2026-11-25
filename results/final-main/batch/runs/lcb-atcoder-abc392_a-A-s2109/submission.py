import sys

def solve():
    data = sys.stdin.read().strip().split()
    if len(data) != 3:
        return
    a = [int(x) for x in data]
    # Check all permutations: (a[0], a[1], a[2]), (a[0], a[2], a[1]), (a[1], a[0], a[2]),
    # (a[1], a[2], a[0]), (a[2], a[0], a[1]), (a[2], a[1], a[0])
    # We need b1 * b2 == b3
    for i in range(3):
        for j in range(3):
            if i == j:
                continue
            for k in range(3):
                if k == i or k == j:
                    continue
                b1, b2, b3 = a[i], a[j], a[k]
                if b1 * b2 == b3:
                    print("Yes")
                    return
    print("No")

if __name__ == "__main__":
    solve()
