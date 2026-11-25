import sys
from collections import Counter

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    n = int(input_data[0])
    a = [int(x) for x in input_data[1:]]
    
    # Count occurrences of each integer
    counts = Counter(a)
    
    # Find persons whose integer occurs exactly once
    # We need the person with the largest integer among those
    best_label = -1
    best_value = -1
    
    for i, val in enumerate(a):
        if counts[val] == 1:
            if val > best_value:
                best_value = val
                best_label = i + 1  # 1-based index
    
    if best_label == -1:
        print("-1")
    else:
        print(best_label)

if __name__ == "__main__":
    solve()
