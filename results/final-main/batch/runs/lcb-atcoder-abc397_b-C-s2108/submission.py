import sys

def solve():
    s = sys.stdin.read().strip()
    insertions = 0
    pattern_pos = 0  # 0-indexed: even positions are 'i', odd positions are 'o'
    
    for char in s:
        # Determine what character should be at pattern_pos
        expected_char = 'i' if pattern_pos % 2 == 0 else 'o'
        
        if char == expected_char:
            # Match! Move to next position
            pattern_pos += 1
        else:
            # Mismatch: we need to insert the expected character
            insertions += 1
            pattern_pos += 1  # After insertion, we move to next position
            # Now try to match the current char again
            expected_char = 'i' if pattern_pos % 2 == 0 else 'o'
            if char == expected_char:
                pattern_pos += 1
    
    # After matching all characters, we need to ensure the total length is even
    # If pattern_pos is odd, we need to insert one more 'o'
    if pattern_pos % 2 == 1:
        insertions += 1
    
    print(insertions)

if __name__ == "__main__":
    solve()
