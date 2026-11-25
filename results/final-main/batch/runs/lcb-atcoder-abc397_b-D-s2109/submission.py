import sys

def solve():
    s = sys.stdin.read().strip()
    n = len(s)
    ans = 0
    for i, c in enumerate(s):
        p = i + ans
        expected = 'i' if p % 2 == 0 else 'o'
        if c != expected:
            ans += 1
    # After processing all characters, if the last position is odd (expects 'o'),
    # we need to add 'o' to complete the pattern
    # Actually, we need to check if the final string ends properly
    # The final position in the ideal string is n + ans
    # If this position is odd, we need to add 'o'
    final_p = n + ans
    if final_p % 2 == 1:
        ans += 1
    print(ans)

if __name__ == "__main__":
    solve()
