import sys

def solve():
    s = sys.stdin.read().strip()
    if not s:
        print("No")
        return

    # Use a stack to track unmatched characters
    stack = []
    for char in s:
        if char in "([{<":
            stack.append(char)
        else:
            # It's a closing bracket
            if not stack:
                print("No")
                return
            top = stack[-1]
            # Check if it matches the top of the stack
            if (top == '(' and char == ')') or \
               (top == '[' and char == ']') or \
               (top == '<' and char == '>'):
                stack.pop()
            else:
                # Mismatch: cannot delete this pair
                print("No")
                return

    # If stack is empty, all brackets were matched and deleted
    if not stack:
        print("Yes")
    else:
        print("No")

if __name__ == "__main__":
    solve()
