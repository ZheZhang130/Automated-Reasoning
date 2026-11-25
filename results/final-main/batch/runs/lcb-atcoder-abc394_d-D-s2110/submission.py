import sys

def solve():
    s = sys.stdin.read().strip()
    n = len(s)
    if n % 2 != 0:
        print("No")
        return
    
    # We need to check if the string can be reduced to empty by repeatedly
    # deleting adjacent matching pairs: (), [], <>
    # This is equivalent to checking if the string is a valid bracket sequence
    # where each type of bracket must match with its corresponding type.
    # We can use a stack-based approach:
    # - When we see an opening bracket, push it onto the stack.
    # - When we see a closing bracket, check if it matches the top of the stack.
    #   If it matches, pop the stack (simulating deletion).
    #   If it doesn't match or stack is empty, then it's invalid.
    # - At the end, the stack must be empty.
    
    stack = []
    matching = {')': '(', ']': '[', '>': '<'}
    
    for char in s:
        if char in '([{<':
            stack.append(char)
        else:
            if not stack:
                print("No")
                return
            top = stack[-1]
            if matching[char] == top:
                stack.pop()
            else:
                print("No")
                return
    
    if not stack:
        print("Yes")
    else:
        print("No")

if __name__ == "__main__":
    solve()
