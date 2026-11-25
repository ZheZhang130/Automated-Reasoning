import sys

def solve():
    s = sys.stdin.read().strip()
    n = len(s)
    count = 0
    
    # We need to find triples (i, j, k) such that:
    # 1 <= i < j < k <= n (1-indexed)
    # j - i = k - j  => 2*j = i + k => j is the midpoint of i and k
    # S[i-1] == 'A', S[j-1] == 'B', S[k-1] == 'C'
    
    # Let's work with 0-indexed positions for implementation:
    # Let i0, j0, k0 be 0-indexed positions.
    # Then i0 < j0 < k0
    # j0 - i0 = k0 - j0 => 2*j0 = i0 + k0
    # S[i0] == 'A', S[j0] == 'B', S[k0] == 'C'
    
    # We can iterate over all possible j0 (positions of 'B')
    # For each j0, we need to count pairs (i0, k0) such that:
    # i0 < j0, k0 > j0, and k0 = 2*j0 - i0
    # Also S[i0] == 'A' and S[k0] == 'C'
    
    # So for each j0 where S[j0] == 'B':
    #   For each i0 < j0 where S[i0] == 'A':
    #     k0 = 2*j0 - i0
    #     If k0 < n and S[k0] == 'C', then we found a valid triple.
    
    for j0 in range(n):
        if s[j0] != 'B':
            continue
        # For this j0, iterate over all i0 < j0 where s[i0] == 'A'
        for i0 in range(j0):
            if s[i0] == 'A':
                k0 = 2 * j0 - i0
                if k0 < n and s[k0] == 'C':
                    count += 1
    
    print(count)

if __name__ == "__main__":
    solve()
