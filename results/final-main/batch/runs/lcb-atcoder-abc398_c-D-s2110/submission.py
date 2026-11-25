import sys
from collections import Counter

def main():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0])
    a = [int(x) for x in data[1:]]
    
    # Count occurrences of each integer
    counts = Counter(a)
    
    # Find integers that occur exactly once
    unique_values = [val for val, count in counts.items() if count == 1]
    
    if not unique_values:
        print(-1)
    else:
        # Find the largest integer among those that occur exactly once
        max_val = max(unique_values)
        # Find the label (1-based index) of the person with this value
        # Since we need the label, and the problem says "the person", 
        # we assume there's only one such person (which is true since count == 1)
        for i, val in enumerate(a):
            if val == max_val:
                print(i + 1)
                break

if __name__ == "__main__":
    main()
