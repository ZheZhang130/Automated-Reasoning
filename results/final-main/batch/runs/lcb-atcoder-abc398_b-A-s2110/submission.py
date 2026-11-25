import sys
from collections import Counter

def solve():
    # Read all integers from stdin
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    # Parse the 7 integers
    cards = [int(x) for x in input_data]
    
    # Count frequencies of each card
    counts = Counter(cards)
    
    # We need to find if there exist x and y (x != y) such that:
    # count[x] >= 3 and count[y] >= 2
    # Note: We can choose any subset of 5 cards, so we just need to check
    # if there's at least one value with count >= 3 and another different value with count >= 2
    
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
    solve()
