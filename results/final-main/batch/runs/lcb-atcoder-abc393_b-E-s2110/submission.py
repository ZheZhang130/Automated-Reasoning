def solve():
    s = input().strip()
    n = len(s)
    count = 0
    
    # Iterate over all possible middle positions j (1-indexed in problem, 0-indexed in Python)
    # In Python 0-indexed: i < j < k, and j - i = k - j means j is midpoint
    # So i = j - d, k = j + d for some d > 0
    for j in range(1, n - 1):
        if s[j] != 'B':
            continue
        
        # Try all possible distances d
        for d in range(1, n - j):
            i = j - d
            k = j + d
            if i >= 0 and k < n:
                if s[i] == 'A' and s[k] == 'C':
                    count += 1
    
    print(count)

if __name__ == "__main__":
    solve()
