import sys

def solve():
    s = sys.stdin.read().strip()
    if not s:
        return
    first_char = s[0]
    print(first_char + "UPC")

if __name__ == "__main__":
    solve()
