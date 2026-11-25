import sys
from bisect import bisect_right

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0])
    a = list(map(int, data[1:]))
    
    total = 0
    for i in range(n):
        bottom = a[i]
        if bottom < 2:
            continue
        max_top = bottom // 2
        count = bisect_right(a, max_top, lo=0, hi=i)
        total += count
    
    print(total)

if __name__ == "__main__":
    solve()
