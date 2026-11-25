def solve():
    s = input().strip()
    n = len(s)
    count = 0
    
    # Iterate over all possible middle positions j (1-indexed in problem, 0-indexed in Python)
    # In 0-indexed: i < j < k, and j - i = k - j => 2*j = i + k
    # So j is the midpoint between i and k
    for j in range(1, n - 1):
        if s[j] != 'B':
            continue
        
        # We need i = j - d and k = j + d for some d > 0
        # i must be at least 0 (0-indexed), so j - d >= 0 => d <= j
        # k must be < n, so j + d < n => d < n - j
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
