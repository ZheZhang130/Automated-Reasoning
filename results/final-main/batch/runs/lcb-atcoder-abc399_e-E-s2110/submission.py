import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    S = input_data[1]
    T = input_data[2]

    # Build the mapping from S to T
    mapping = {}
    for i in range(N):
        if S[i] in mapping:
            if mapping[S[i]] != T[i]:
                print(-1)
                return
        else:
            mapping[S[i]] = T[i]
    
    # Check for cycles in the mapping
    # We need to detect if there's a cycle like a->b->a
    # But self-loops like a->a are fine
    
    visited = set()
    for c in mapping:
        if c not in visited:
            current = c
            path = []
            while current not in visited and current in mapping:
                visited.add(current)
                path.append(current)
                current = mapping[current]
            
            # If we reached a character that's in the path AND it's not a self-loop, we have a cycle
            # A self-loop is when current == c (the starting character)
            if current in path and current != c:
                print(-1)
                return
    
    # Count the number of characters that need to be changed
    count = 0
    for c in mapping:
        if mapping[c] != c:
            count += 1
    
    print(count)

solve()
