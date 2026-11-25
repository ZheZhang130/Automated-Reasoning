import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0])
    s = data[1]
    t = data[2]
    
    count = 0
    for i in range(n):
        if s[i] != t[i]:
            count += 1
    
    print(count)

if __name__ == "__main__":
    solve()
