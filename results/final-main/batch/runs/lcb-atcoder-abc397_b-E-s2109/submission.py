import sys

def solve():
    s = sys.stdin.read().strip()
    n = len(s)
    
    # We need to scan left to right and track expected character
    # Start expecting 'i' at position 1 (odd)
    # After each character (inserted or from input), toggle expectation
    
    expected = 'i'  # Next expected character
    insertions = 0
    
    for c in s:
        if c == expected:
            # Match found, consume this character
            expected = 'o' if expected == 'i' else 'i'
        else:
            # Mismatch, insert the expected character
            insertions += 1
            expected = 'o' if expected == 'i' else 'i'
    
    # After processing all characters, if we expect 'o', we need to insert it
    if expected == 'o':
        insertions += 1
    
    print(insertions)

if __name__ == "__main__":
    solve()
