import sys

def solve():
    s = sys.stdin.read().strip()
    expected = 'i'  # Start expecting 'i'
    ans = 0
    for c in s:
        if c == expected:
            # Match, consume this character and move to next expected
            expected = 'o' if expected == 'i' else 'i'
        else:
            # Mismatch, insert the expected character
            ans += 1
            expected = 'o' if expected == 'i' else 'i'
    # After processing all characters, if we still expect 'o', we need to insert it
    if expected == 'o':
        ans += 1
    print(ans)

if __name__ == "__main__":
    solve()
