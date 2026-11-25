import sys

def solve():
    s = sys.stdin.read().strip()
    n = len(s)
    # Convert to 0-based indexing for internal logic
    # We need 1 <= i < j < k <= n (1-based)
    # j - i = k - j  => 2*j = i + k  => j is the midpoint of i and k
    # In 0-based: let i0 = i-1, j0 = j-1, k0 = k-1
    # Then (j0+1) - (i0+1) = (k0+1) - (j0+1) => j0 - i0 = k0 - j0 => 2*j0 = i0 + k0
    # So j0 is the midpoint of i0 and k0.
    
    # We can iterate over all possible j positions (0-based)
    # For each j, if s[j] == 'B', then we need to count:
    #   number of i < j with s[i] == 'A'
    #   number of k > j with s[k] == 'C'
    # such that j - i = k - j => k = 2*j - i
    # So for each j, we iterate over possible i < j where s[i] == 'A'
    # and check if k = 2*j - i is valid and s[k] == 'C'
    
    count = 0
    for j in range(n):
        if s[j] != 'B':
            continue
        # j is the middle index (0-based)
        # We need i < j such that s[i] == 'A' and k = 2*j - i < n and s[k] == 'C'
        # Also i >= 0 (which is true since i < j and j >= 0)
        # And k > j (which is true if i < j, since k = 2*j - i > 2*j - j = j)
        for i in range(j):
            if s[i] == 'A':
                k = 2 * j - i
                if k < n and s[k] == 'C':
                    count += 1
    print(count)

if __name__ == "__main__":
    solve()
