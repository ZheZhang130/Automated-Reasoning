import sys

def solve():
    s = sys.stdin.read().strip()
    n = len(s)
    count = 0
    # Iterate over all possible middle positions j (0-indexed)
    for j in range(n):
        if s[j] != 'B':
            continue
        # For a fixed j, we need i < j and k > j such that j - i = k - j
        # This implies k = 2*j - i
        # Also i must be such that s[i] == 'A' and k < n and s[k] == 'C'
        # Let d = j - i, then i = j - d, k = j + d
        # d must be at least 1 (since i < j)
        # i >= 0 => j - d >= 0 => d <= j
        # k < n => j + d < n => d < n - j
        # So d ranges from 1 to min(j, n - 1 - j)
        max_d = min(j, n - 1 - j)
        for d in range(1, max_d + 1):
            i = j - d
            k = j + d
            if s[i] == 'A' and s[k] == 'C':
                count += 1
    print(count)

if __name__ == "__main__":
    solve()
