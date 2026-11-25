import sys

def solve():
    s = sys.stdin.read().strip()
    n = len(s)
    if n == 0:
        print("Yes")
        return

    # We need to check if we can reduce the string to empty by deleting ()
    # [], <> in any order.
    # Key insight: The relative order of different bracket types doesn't matter
    # as long as they form valid pairs. We can think of this as:
    # 1. First, remove all () pairs (matching adjacent or nested).
    # 2. Then, remove all [] pairs from the remaining string.
    # 3. Then, remove all <> pairs from the remaining string.
    # If we end up with empty string, then Yes.
    #
    # However, the order of removal matters. But note:
    # If we have a valid sequence, there exists SOME order.
    # Actually, we can process in any order? Let's think.
    # Consider: ([]) -> remove [] first -> () -> remove () -> empty.
    # Consider: ()[] -> remove () first -> [] -> remove [] -> empty.
    # So order doesn't matter for disjoint pairs.
    # What about nested? ([]) vs [()]?
    # ([]) is valid. [()] is valid.
    # The problem is when we have mismatched types like ([<)]>.
    #
    # Algorithm:
    # We can simulate the process by repeatedly finding any valid pair and removing it.
    # But that might be slow (O(n^2)).
    #
    # Better approach:
    # Notice that the operations allow removing ANY contiguous substring that is a valid pair.
    # This means we can remove pairs that are not necessarily adjacent in the original string,
    # as long as the characters between them have been removed.
    #
    # This is equivalent to: can we match every character with a partner of the same type,
    # such that the matching respects the nesting structure?
    # But wait, the types are different. We can't match ( with [.
    #
    # Actually, the key is: we can only remove () , [] , <>.
    # So a '(' must be matched with a ')', etc.
    # And the matching must be valid in the sense that if we have ( ... ),
    # the ... part must be reducible to empty.
    #
    # This is exactly the definition of a valid bracket sequence, but with multiple types.
    # However, the catch is: can we interleave different types?
    # Example: ([]) is valid. What about ([)]?
    # In ([)]:
    # - We cannot remove () because the ) is after the ].
    # - We cannot remove [] because the ] is after the (.
    # - We cannot remove <> because there is no <.
    # So ([)] is invalid.
    #
    # But what about ([<)]>?
    # We can remove <> first? But <> is not contiguous initially.
    # The problem says: "contiguous substring of T".
    # So we can only remove contiguous pairs.
    #
    # This means: we must remove pairs that are adjacent (after previous removals).
    #
    # Approach:
    # We can use a stack. But the stack needs to handle multiple types.
    # However, the types are independent. We can process each type separately?
    # No, because removals affect contiguity.
    #
    # Insight:
    # The relative order of different bracket types doesn't interfere with each other's validity,
    # EXCEPT that they share the same "nesting" structure.
    # Actually, we can think of it as: the string is valid if and only if:
    # 1. When we ignore all brackets of type other than (), the () part is valid.
    # 2. Similarly for [] and <>.
    # But that's not sufficient. Consider: ([]) -> if we ignore [], we get () which is valid.
    # If we ignore (), we get [] which is valid.
    # But what about: ([)]?
    # Ignore (): we get [ ] -> valid? But the original is ([)] which is invalid.
    # So that condition is not enough.
    #
    # Correct approach:
    # We can simulate the reduction. But we need an efficient way.
    # Notice: we can remove any valid pair. So we can greedily remove pairs?
    # But which pair to remove first?
    # Actually, the order doesn't matter for the final result? 
    # Let me check: 
    # Suppose we have two disjoint valid pairs: () and [].
    # We can remove () first, then []. Or [] first, then (). Same result.
    # What if they are nested? ([]) -> remove [] first -> () -> remove ().
    # Or remove () first? But () is not contiguous until [] is removed.
    # So we must remove the inner pair first.
    #
    # Therefore, the reduction is deterministic: we must remove the innermost pairs first.
    # This suggests using a stack.
    #
    # Stack approach:
    # Traverse the string. For each character:
    #   - If it's an opening bracket, push to stack.
    #   - If it's a closing bracket:
    #       - Check if the top of the stack is the matching opening bracket.
    #       - If yes, pop the stack (we found a pair).
    #       - If no, then we have a mismatch. But wait, what if the matching opening bracket
    #         is not at the top? That means there are other brackets in between that haven't been removed.
    #         But we can only remove contiguous pairs. So if the matching opening bracket is not at the top,
    #         it means there are unmatched brackets in between, so we cannot remove the pair yet.
    #         And since we can only remove contiguous pairs, we must remove the innermost pairs first.
    #         Therefore, if the top doesn't match, then the current closing bracket cannot be matched
    #         with any previous opening bracket (because the ones in between are not removed yet).
    #         So it's invalid.
    #
    # But wait, what about different types? 
    # Example: ([])
    # - Push '('.
    # - See '[': push '['.
    # - See ']': top is '[', which matches. Pop '['.
    # - See ')': top is '(', which matches. Pop '('.
    # Stack empty -> valid.
    #
    # Example: ([<)]>
    # - Push '('.
    # - Push '['.
    # - Push '<'.
    # - See ')': top is '<', which does not match. So invalid?
    # But wait, the sample says ([<)]> is invalid, and our reasoning says invalid.
    #
    # However, consider: ([])<>()
    # - Push '('.
    # - Push '['.
    # - See ']': matches, pop.
    # - See ')': matches, pop.
    # - Push '<'.
    # - Push '>'.
    # - See ')': wait, the string is ([])<>()
    #   Characters: ( [ ] ) < > ( )
    #   Step by step:
    #   - '(': push '('
    #   - '[': push '['
    #   - ']': matches top '[', pop. Stack: ['(']
    #   - ')': matches top '(', pop. Stack: []
    #   - '<': push '<'
    #   - '>': matches top '<', pop. Stack: []
    #   - '(': push '('
    #   - ')': matches top '(', pop. Stack: []
    #   Empty -> valid.
    #
    # But what about: ()[]
    # - '(': push '('
    # - ')': matches, pop. Stack: []
    # - '[': push '['
    # - ']': matches, pop. Stack: []
    # Valid.
    #
    # What about: [()]
    # - '[': push '['
    # - '(': push '('
    # - ')': matches, pop. Stack: ['[']
    # - ']': matches, pop. Stack: []
    # Valid.
    #
    # What about: ) (
    # - ')': stack empty, no match -> invalid.
    #
    # So the algorithm is:
    #   Use a stack. For each char:
    #     If opening: push.
    #     If closing:
    #       If stack not empty and top matches: pop.
    #       Else: invalid.
    #   After processing, if stack is empty: valid, else invalid.
    #
    # But wait, what about the case where the matching opening bracket is not at the top?
    # Example: ( [ ) ]
    # - '(': push '('
    # - '[': push '['
    # - ')': top is '[', which does not match ')'. So invalid.
    # But is it invalid? 
    # The string is ( [ ) ].
    # Can we remove any pair? 
    # - () is not contiguous (there is [ in between).
    # - [] is not contiguous (there is ) in between).
    # - <> doesn't exist.
    # So we cannot remove any pair. Thus invalid.
    # Our algorithm says invalid. Correct.
    #
    # Another example: ( ) [ ]
    # - '(': push '('
    # - ')': matches, pop. Stack: []
    # - '[': push '['
    # - ']': matches, pop. Stack: []
    # Valid. Correct.
    #
    # So the stack approach works?
    # But wait, the problem allows removing ANY contiguous substring that is a valid pair.
    # And our stack approach only removes adjacent pairs (after previous removals).
    # Is that sufficient?
    # Yes, because if we have a valid pair that is not adjacent, it means there are characters in between.
    # But those characters must be removed first (since they are part of the string and we need to make the pair contiguous).
    # And the stack approach removes the innermost pairs first, which is exactly what we need.
    #
    # Therefore, the stack approach is correct.
    #
    # Implementation:
    #   Map each closing bracket to its matching opening bracket.
    #   Use a stack of characters.
    #   Traverse the string.
    #   If char is opening: push.
    #   If char is closing:
    #       If stack empty or top != matching opening: return "No"
    #       Else: pop.
    #   After traversal, if stack empty: "Yes", else "No".
    #
    # But wait, what about the case where we have unmatched opening brackets?
    # The stack will not be empty, so we return "No". Correct.
    #
    # Let's test with sample 3: ())
    # - '(': push '('
    # - ')': matches, pop. Stack: []
    # - ')': stack empty -> invalid. Return "No". Correct.
    #
    # Sample 2: ([<)]>
    # - '(': push '('
    # - '[': push '['
    # - '<': push '<'
    # - ')': top is '<', which does not match ')'. Return "No". Correct.
    #
    # So the algorithm is:
    #   stack = []
    #   mapping = {')': '(', ']': '[', '>': '<'}
    #   for char in s:
    #       if char in '([{<':
    #           stack.append(char)
    #       else:
    #           if not stack or stack[-1] != mapping[char]:
    #               print("No")
    #               return
    #           stack.pop()
    #   if not stack:
    #       print("Yes")
    #   else:
    #       print("No")
    #
    # But wait, what about the case where we have extra opening brackets at the end?
    # The stack will not be empty, so we return "No". Correct.
    #
    # However, there's a catch: the problem allows removing pairs in any order, but the stack approach
    # only removes pairs that are adjacent (after previous removals). Is that sufficient?
    # Yes, because if a pair is not adjacent, we must remove the characters in between first.
    # And the stack approach does that by removing innermost pairs first.
    #
    # Therefore, the solution is correct.

    mapping = {')': '(', ']': '[', '>': '<'}
    stack = []
    for char in s:
        if char in '([{<':
            stack.append(char)
        else:
            if not stack or stack[-1] != mapping[char]:
                print("No")
                return
            stack.pop()
    
    if not stack:
        print("Yes")
    else:
        print("No")

solve()
