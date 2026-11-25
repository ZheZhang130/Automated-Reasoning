import sys

def solve():
    s = sys.stdin.readline().strip()
    if not s:
        return
    print(s[0] + "UPC")

if __name__ == "__main__":
    solve()
