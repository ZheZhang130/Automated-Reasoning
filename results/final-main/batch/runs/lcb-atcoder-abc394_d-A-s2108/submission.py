import sys

def solve():
    s = sys.stdin.read().strip()
    n = len(s)
    if n == 0:
        print("Yes")
        return

    # We need to check if we can reduce the string to empty by deleting (), [], <>
    # This is equivalent to checking if the string is a valid bracket sequence
    # where we can delete any matching pair in any order.
    # 
    # Key insight: The order of deletion doesn't matter for the final result (empty or not).
    # We can use a stack-based approach.
    #
    # However, there's a catch: we can delete ANY matching pair, not just the innermost ones.
    # But actually, for bracket sequences, the standard stack approach works because:
    # - If we have a valid sequence, the stack will be empty at the end.
    # - If we have an invalid sequence, the stack won't be empty.
    #
    # But wait, the problem allows deleting ANY matching pair, not just adjacent ones in the original string.
    # Actually, the operation says "contiguous substring", so we can only delete adjacent matching pairs.
    #
    # Let's think again:
    # We can delete (), [], <> as contiguous substrings.
    # After deletion, the string is concatenated, so new adjacent pairs might form.
    #
    # This is exactly the definition of a valid bracket sequence!
    # A string is a valid bracket sequence if and only if:
    # 1. Every opening bracket has a matching closing bracket.
    # 2. The brackets are properly nested.
    #
    # We can check this with a stack:
    # - When we see an opening bracket, push it onto the stack.
    # - When we see a closing bracket:
    #   - If the stack is empty, it's invalid.
    #   - If the top of the stack is the matching opening bracket, pop it.
    #   - Otherwise, it's invalid.
    #
    # At the end, if the stack is empty, it's valid.
    #
    # Let's verify with the samples:
    # Sample 1: ([])<>()
    #   - '(': push '('
    #   - '[': push '['
    #   - ']': matches top '[', pop -> stack: ['(']
    #   - ')': matches top '(', pop -> stack: []
    #   - '<': push '<'
    #   - '>': matches top '<', pop -> stack: []
    #   - '(': push '('
    #   - ')': matches top '(', pop -> stack: []
    #   - Empty stack -> Yes
    #
    # Sample 2: ([<)]>
    #   - '(': push '('
    #   - '[': push '['
    #   - '<': push '<'
    #   - ')': top is '<', not matching -> No
    #
    # Sample 3: ())
    #   - '(': push '('
    #   - ')': matches top '(', pop -> stack: []
    #   - ')': stack empty -> No
    #
    # This matches all samples!

    stack = []
    pairs = {')': '(', ']': '[', '>': '<'}
    
    for char in s:
        if char in '([{<':
            stack.append(char)
        else:
            if not stack:
                print("No")
                return
            top = stack[-1]
            if pairs[char] == top:
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
