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
    
    # Find people whose integer appears exactly once
    unique_people = []
    for i, val in enumerate(a):
        if counts[val] == 1:
            unique_people.append((val, i + 1))  # (value, label)
    
    if not unique_people:
        print(-1)
    else:
        # Find the person with the greatest integer among unique ones
        max_val = -1
        max_label = -1
        for val, label in unique_people:
            if val > max_val:
                max_val = val
                max_label = label
        print(max_label)

if __name__ == "__main__":
    main()
