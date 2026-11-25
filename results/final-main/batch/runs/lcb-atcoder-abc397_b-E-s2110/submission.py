import sys

def solve():
    s = sys.stdin.read().strip()
    n = len(s)
    ans = 0
    for i, c in enumerate(s):
        pos = i + 1  # 1-based position
        expected = 'i' if pos % 2 == 1 else 'o'
        if c != expected:
            ans += 1
    print(ans)

if __name__ == "__main__":
    solve()
