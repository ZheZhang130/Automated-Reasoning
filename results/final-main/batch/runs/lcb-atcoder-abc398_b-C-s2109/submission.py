import sys
from collections import Counter

def main():
    # Read all integers from standard input
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    # Parse the 7 card values
    cards = [int(x) for x in input_data]
    
    # Count occurrences of each card value
    counts = Counter(cards)
    
    # Check if a full house can be formed
    # A full house requires one value with at least 3 cards and a different value with at least 2 cards
    possible = False
    for val1, count1 in counts.items():
        if count1 >= 3:
            for val2, count2 in counts.items():
                if val1 != val2 and count2 >= 2:
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
