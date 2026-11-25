import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    A = list(map(int, input_data[1:]))
    
    last_seen = {}
    min_len = float('inf')
    
    for i in range(N):
        val = A[i]
        if val in last_seen:
            prev_i = last_seen[val]
            length = i - prev_i + 1
            if length < min_len:
                min_len = length
        last_seen[val] = i
    
    if min_len == float('inf'):
        print(-1)
    else:
        print(min_len)

if __name__ == "__main__":
    solve()
