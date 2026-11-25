import sys
from collections import Counter

def solve():
    # Read all integers from stdin
    data = sys.stdin.read().split()
    if not data:
        return
    
    # Parse the 7 integers
    A = list(map(int, data))
    
    # Count frequencies of each card value
    counts = Counter(A)
    
    # We need to choose 5 cards forming a full house:
    # - Three cards with value x
    # - Two cards with value y
    # where x != y
    
    # Strategy: Try all possible pairs of (x, y) from the available cards
    # For each pair, check if we have at least 3 cards of x and 2 cards of y
    
    # Get all unique card values present
    unique_values = list(counts.keys())
    
    can_form_full_house = False
    
    # Try each pair of distinct values (x, y)
    for x in unique_values:
        for y in unique_values:
            if x == y:
                continue
            
            # Check if we have at least 3 of x and 2 of y
            if counts[x] >= 3 and counts[y] >= 2:
                can_form_full_house = True
                break
    
    if can_form_full_house:
        print("Yes")
    else:
        print("No")

if __name__ == "__main__":
    solve()
