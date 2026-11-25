import sys
from collections import Counter

def main():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0])
    a = [int(x) for x in data[1:]]
    
    counts = Counter(a)
    
    unique_values = [val for val, count in counts.items() if count == 1]
    
    if not unique_values:
        print(-1)
    else:
        max_val = max(unique_values)
        # Find the label (1-indexed position) of the person with max_val
        # Since max_val occurs exactly once, we can just find its index
        label = a.index(max_val) + 1
        print(label)

if __name__ == "__main__":
    main()
