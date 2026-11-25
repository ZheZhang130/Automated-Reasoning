import sys
from collections import deque

def main():
    input = sys.stdin.read
    data = input().split()
    idx = 0
    Q = int(data[idx])
    idx += 1
    
    # Stack: we'll use a list where the end is the top
    stack = deque([0] * 100)
    
    results = []
    
    for _ in range(Q):
        c = int(data[idx])
        idx += 1
        
        if c == 1:
            x = int(data[idx])
            idx += 1
            stack.append(x)
        else:
            top = stack.pop()
            results.append(str(top))
    
    print('\n'.join(results))

if __name__ == "__main__":
    main()
