import sys

def solve():
    s = sys.stdin.read().strip()
    stack = []
    pairs = {')': '(', ']': '[', '>': '<'}
    for ch in s:
        if ch in '([{<':
            stack.append(ch)
        else:
            if not stack:
                print("No")
                return
            top = stack[-1]
            if pairs[ch] != top:
                print("No")
                return
            stack.pop()
    if stack:
        print("No")
    else:
        print("Yes")

if __name__ == "__main__":
    solve()
