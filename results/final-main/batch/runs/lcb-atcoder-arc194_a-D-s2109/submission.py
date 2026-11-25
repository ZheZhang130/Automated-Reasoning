import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0])
    a = [int(x) for x in data[1:]]
    
    stack = []
    for x in a:
        if not stack:
            stack.append(x)
        else:
            if stack[-1] < 0:
                stack.pop()
            else:
                stack.append(x)
    
    print(sum(stack))

if __name__ == "__main__":
    solve()
