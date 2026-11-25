import sys

def solve():
    # Read input from stdin
    line = sys.stdin.read().strip()
    if not line:
        return
    parts = list(map(int, line.split()))
    A = parts
    
    # Check all permutations of A
    # We need to check if any permutation (B1, B2, B3) satisfies B1 * B2 = B3
    # Since there are only 3 elements, we can check all 6 permutations manually
    # or use itertools.permutations
    
    from itertools import permutations
    
    for b1, b2, b3 in permutations(A):
        if b1 * b2 == b3:
            print("Yes")
            return
    
    print("No")

if __name__ == "__main__":
    solve()
