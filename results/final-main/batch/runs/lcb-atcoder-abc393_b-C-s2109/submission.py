import sys

def solve():
    s = sys.stdin.read().strip()
    n = len(s)
    count = 0
    
    # Iterate over each position as the middle element j (0-indexed)
    for j in range(n):
        if s[j] != 'B':
            continue
        
        # Determine the maximum possible gap d
        # Left endpoint: j - d >= 0  => d <= j
        # Right endpoint: j + d < n  => d < n - j
        max_d = min(j, n - 1 - j)
        
        # Check all valid gaps
        for d in range(1, max_d + 1):
            i = j - d
            k = j + d
            if s[i] == 'A' and s[k] == 'C':
                count += 1
    
    print(count)

if __name__ == "__main__":
    solve()
