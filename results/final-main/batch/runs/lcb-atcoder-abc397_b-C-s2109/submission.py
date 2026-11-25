import sys

def solve():
    s = sys.stdin.read().strip()
    insertions = 0
    expected = 'i'  # Next character we expect in the pattern
    
    for char in s:
        if char == expected:
            # Match found, move to next expected character
            if expected == 'i':
                expected = 'o'
            else:
                expected = 'i'
        else:
            # Mismatch: insert the expected character, then match current char
            insertions += 1
            # After insertion, we still need to match the current char
            # But now the expected character for the next position is the opposite
            # of what we just inserted. Since we inserted 'expected', the next
            # expected is the opposite. Then we match 'char' which must be the
            # new expected (since it's the only option left).
            if expected == 'i':
                expected = 'o'
            else:
                expected = 'i'
    
    # After processing all characters, if we expect 'o', we need to insert it
    if expected == 'o':
        insertions += 1
    
    print(insertions)

if __name__ == "__main__":
    solve()
