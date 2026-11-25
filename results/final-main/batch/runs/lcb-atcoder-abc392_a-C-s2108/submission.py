import sys

def solve():
    data = sys.stdin.read().strip().split()
    if not data:
        return
    a = [int(x) for x in data]
    a.sort()
    if a[0] * a[1] == a[2]:
        print("Yes")
    else:
        print("No")

if __name__ == "__main__":
    solve()
