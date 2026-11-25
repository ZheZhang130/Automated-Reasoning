import sys
from collections import Counter

def solve():
    # Read all integers from standard input
    try:
        data = sys.stdin.read().split()
        if not data:
            return
        cards = [int(x) for x in data]
    except Exception:
        return

    # Count occurrences of each card value
    counts = Counter(cards)
    
    # Check if there exists a full house:
    # One value appears at least 3 times, another different value appears at least 2 times
    possible = False
    for x in counts:
        if counts[x] >= 3:
            for y in counts:
                if x != y and counts[y] >= 2:
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
