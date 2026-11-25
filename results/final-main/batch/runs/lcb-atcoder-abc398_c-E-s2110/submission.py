import sys
from collections import Counter

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0])
    a = list(map(int, data[1:]))
    
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
        # Find the person with the greatest integer
        unique_people.sort(key=lambda x: x[0], reverse=True)
        print(unique_people[0][1])

if __name__ == "__main__":
    solve()
