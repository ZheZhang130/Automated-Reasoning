import sys
from collections import Counter

def solve():
    # Read all integers from stdin
    try:
        data = sys.stdin.read().split()
        if not data:
            return
        A = [int(x) for x in data]
    except ValueError:
        return

    if len(A) != 7:
        return

    # Count frequencies of each card value
    counts = Counter(A)
    
    # We need exactly one value with count >= 3 and another different value with count >= 2
    # Check if we can form a full house
    possible = False
    
    # Get values that appear at least 3 times
    triple_values = [v for v, c in counts.items() if c >= 3]
    # Get values that appear at least 2 times
    pair_values = [v for v, c in counts.items() if c >= 2]
    
    # We need one from triple_values and one from pair_values that are different
    for t in triple_values:
        for p in pair_values:
            if t != p:
                possible = True
                break
        if possible:
            break
    
    if possible:
        print("Yes")
    else:
        print("No")

if __name__ == "__main__":
    solve()
