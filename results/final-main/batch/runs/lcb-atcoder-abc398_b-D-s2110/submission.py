import sys
from collections import Counter

def solve():
    # Read all integers from standard input
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    # Parse the 7 integers
    cards = [int(x) for x in input_data]
    
    # Count frequencies of each card value
    counts = Counter(cards)
    
    # Get the counts sorted
    count_values = sorted(counts.values(), reverse=True)
    
    # We need at least one value with count >= 3 and another with count >= 2
    # The two largest counts must satisfy: max_count >= 3 and second_max_count >= 2
    # Need at least 2 distinct values for a full house
    
    if len(count_values) >= 2 and count_values[0] >= 3 and count_values[1] >= 2:
        print("Yes")
    else:
        print("No")

if __name__ == "__main__":
    solve()
