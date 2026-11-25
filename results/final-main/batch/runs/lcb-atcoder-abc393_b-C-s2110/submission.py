import sys

def solve():
    s = sys.stdin.read().strip()
    n = len(s)
    count = 0
    
    # Iterate over each possible middle position j (0-indexed)
    for j in range(1, n - 1):
        if s[j] != 'B':
            continue
        
        # Iterate over possible gap d
        # Left index: i = j - d
        # Right index: k = j + d
        # Constraints: i >= 0 and k < n
        # So d <= j and d <= n - 1 - j
        max_d = min(j, n - 1 - j)
        
        for d in range(1, max_d + 1):
            i = j - d
            k = j + d
            if s[i] == 'A' and s[k] == 'C':
                count += 1
    
    print(count)

if __name__ == "__main__":
    solve()
