import sys

def solve():
    # Read input from stdin
    line = sys.stdin.read().strip()
    if not line:
        return
    parts = line.split()
    if len(parts) != 3:
        return
    a1, a2, a3 = map(int, parts)
    
    # We need to check if any permutation (b1, b2, b3) satisfies b1 * b2 = b3
    # The permutations of (a1, a2, a3) are:
    # (a1, a2, a3), (a1, a3, a2), (a2, a1, a3), (a2, a3, a1), (a3, a1, a2), (a3, a2, a1)
    # But we only care about b1 * b2 = b3, so we check all 6 permutations
    
    nums = [a1, a2, a3]
    from itertools import permutations
    
    for p in permutations(nums):
        if p[0] * p[1] == p[2]:
            print("Yes")
            return
    
    print("No")

if __name__ == "__main__":
    solve()
