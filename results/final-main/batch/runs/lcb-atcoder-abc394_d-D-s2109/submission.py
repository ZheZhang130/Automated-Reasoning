import sys

def solve():
    s = sys.stdin.read().strip()
    n = len(s)
    if n % 2 != 0:
        print("No")
        return

    # Mapping of opening brackets to their matching closing brackets
    pairs = {'(': ')', '[': ']', '<': '>'}
    
    stack = []
    for char in s:
        if char in pairs:
            # char is an opening bracket
            stack.append(char)
        else:
            # char is a closing bracket
            if stack and stack[-1] in pairs and pairs[stack[-1]] == char:
                stack.pop()
            else:
                stack.append(char)
    
    if not stack:
        print("Yes")
    else:
        print("No")

if __name__ == "__main__":
    solve()
