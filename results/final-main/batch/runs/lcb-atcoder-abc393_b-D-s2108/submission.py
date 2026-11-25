import sys

def solve():
    s = sys.stdin.read().strip()
    n = len(s)
    count = 0
    # Iterate over all possible middle points j (0-indexed)
    for j in range(1, n - 1):
        if s[j] != 'B':
            continue
        # Check for A at i = j - d and C at k = j + d
        d = 1
        while j - d >= 0 and j + d < n:
            if s[j - d] == 'A' and s[j + d] == 'C':
                count += 1
            d += 1
    print(count)

if __name__ == "__main__":
    solve()
