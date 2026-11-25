import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    n = int(input_data[0])
    a = [int(x) for x in input_data[1:]]
    
    last_pos = {}
    min_len = float('inf')
    
    for i, val in enumerate(a):
        if val in last_pos:
            length = i - last_pos[val] + 1
            if length < min_len:
                min_len = length
        last_pos[val] = i
    
    if min_len == float('inf'):
        print(-1)
    else:
        print(min_len)

if __name__ == "__main__":
    solve()
