import sys

def solve():
    s = sys.stdin.read().strip()
    insertions = 0
    expected = 'i'  # 1st, 3rd, ... positions should be 'i'
    
    for char in s:
        if char == expected:
            # Match found, move to next expected
            expected = 'o' if expected == 'i' else 'i'
        else:
            # Mismatch: insert the expected character
            insertions += 1
            expected = 'o' if expected == 'i' else 'i'
            # Now the current char must match the new expected
            if char == expected:
                expected = 'o' if expected == 'i' else 'i'
            else:
                # This shouldn't happen based on problem constraints
                # but if it did, we'd need to insert again
                insertions += 1
                expected = 'o' if expected == 'i' else 'i'
    
    # After processing all characters, if we expect 'o', we need to insert it
    if expected == 'o':
        insertions += 1
    
    print(insertions)

if __name__ == "__main__":
    solve()
