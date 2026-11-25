import sys

def solve():
    s = sys.stdin.read().strip()
    
    # We need to insert characters to make the string valid
    # A valid string has pattern ioioio...
    # We iterate through the string and track the expected character
    # If we see the wrong character, we insert the expected one (count++ and don't advance)
    # If we see the right character, we advance and switch expected
    
    ans = 0
    expected = 'i'  # First character should be 'i'
    for c in s:
        if c == expected:
            # Correct character, advance to next expected
            expected = 'o' if expected == 'i' else 'i'
        else:
            # Wrong character, insert the expected one
            ans += 1
            # Don't advance in s, but switch expected
            expected = 'o' if expected == 'i' else 'i'
    
    # After processing, if the last expected character is 'i', we need to insert 'o'
    if expected == 'i':
        ans += 1
    
    print(ans)

if __name__ == "__main__":
    solve()
