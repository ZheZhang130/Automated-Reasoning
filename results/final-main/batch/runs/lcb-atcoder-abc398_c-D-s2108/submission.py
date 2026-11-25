import sys
from collections import Counter

def main():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0])
    a = [int(x) for x in data[1:]]
    
    counts = Counter(a)
    
    # Filter people whose integer occurs exactly once
    unique_people = [(i, val) for i, val in enumerate(a, start=1) if counts[val] == 1]
    
    if not unique_people:
        print(-1)
    else:
        # Find the one with the greatest integer
        max_val = max(val for _, val in unique_people)
        # Find the label of the person with that max value
        # Since we want the label, and there's only one person with max_val among unique ones
        for label, val in unique_people:
            if val == max_val:
                print(label)
                break

if __name__ == "__main__":
    main()
