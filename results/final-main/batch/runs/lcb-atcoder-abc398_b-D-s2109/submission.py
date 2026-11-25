import sys
from collections import Counter

def main():
    # Read all integers from standard input
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    # Parse the seven integers
    cards = [int(x) for x in input_data]
    
    # Count frequencies of each card value
    counts = Counter(cards)
    
    # Check if we can form a full house:
    # We need one value with at least 3 occurrences and another different value with at least 2 occurrences.
    # Since we have exactly 7 cards, and we need 5 for the full house, we check:
    # - Is there a value with count >= 3?
    # - Is there a different value with count >= 2?
    
    has_triple = False
    has_pair = False
    triple_value = None
    pair_value = None
    
    for value, count in counts.items():
        if count >= 3:
            has_triple = True
            triple_value = value
        if count >= 2:
            has_pair = True
            pair_value = value
    
    # Check if we have both a triple and a pair of different values
    if has_triple and has_pair and triple_value != pair_value:
        print("Yes")
    else:
        print("No")

if __name__ == "__main__":
    main()
