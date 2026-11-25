import sys
from collections import deque

def main():
    input = sys.stdin.read
    data = input().split()
    idx = 0
    Q = int(data[idx])
    idx += 1
    
    # Stack initialized with 100 cards labeled 0
    stack = deque(['0'] * 100)
    
    results = []
    
    for _ in range(Q):
        c = int(data[idx])
        idx += 1
        
        if c == 1:
            x = int(data[idx])
            idx += 1
            stack.appendleft(str(x))
        else:
            top = stack.popleft()
            results.append(top)
    
    print('\n'.join(results))

if __name__ == "__main__":
    main()
