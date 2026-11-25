import sys
from collections import Counter

def main():
    # Read all integers from standard input
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    # Parse the seven card values
    cards = [int(x) for x in input_data]
    
    # Count occurrences of each card value
    counts = Counter(cards)
    
    # Check if a full house can be formed
    # A full house requires: one value with at least 3 cards, 
    # and a different value with at least 2 cards
    possible = False
    for x, count_x in counts.items():
        if count_x >= 3:
            for y, count_y in counts.items():
                if x != y and count_y >= 2:
                    possible = True
                    break
        if possible:
            break
    
    if possible:
        print("Yes")
    else:
        print("No")

if __name__ == "__main__":
    main()
