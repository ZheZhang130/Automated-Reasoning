import sys
from collections import Counter

def solve():
    # Read all integers from stdin
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    # Parse the 7 integers
    A = list(map(int, input_data))
    
    # Count frequencies of each card
    counts = Counter(A)
    
    # A full house requires exactly two distinct values:
    # one appearing 3 times, and another appearing 2 times.
    # We need to check if we can form such a combination from the 7 cards.
    
    # Strategy:
    # We need to find if there exist two distinct values x and y such that:
    # - count[x] >= 3
    # - count[y] >= 2
    # And we can choose 3 of x and 2 of y.
    
    # Since we have 7 cards and need to choose 5, we just need to check
    # if there are at least two distinct values with sufficient counts.
    
    # Let's collect all values that have count >= 3 and count >= 2
    candidates_3 = [val for val, count in counts.items() if count >= 3]
    candidates_2 = [val for val, count in counts.items() if count >= 2]
    
    # We need one value from candidates_3 and one from candidates_2, and they must be different
    for x in candidates_3:
        for y in candidates_2:
            if x != y:
                print("Yes")
                return
    
    print("No")

if __name__ == "__main__":
    solve()
