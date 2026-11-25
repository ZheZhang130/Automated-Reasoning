import sys

def solve():
    s = sys.stdin.read().strip()
    n = len(s)
    ans = 0
    for i, c in enumerate(s):
        pos = i + 1  # 1-based position
        if pos % 2 == 1:  # odd position, should be 'i'
            if c != 'i':
                ans += 1
        else:  # even position, should be 'o'
            if c != 'o':
                ans += 1
    print(ans)

if __name__ == "__main__":
    solve()
