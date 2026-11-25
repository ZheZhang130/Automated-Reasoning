import sys
from collections import deque

def main():
    # Read all input from stdin
    input_data = sys.stdin.read().split()
    
    if not input_data:
        return
    
    iterator = iter(input_data)
    
    try:
        Q = int(next(iterator))
    except StopIteration:
        return
    
    # Initial stack: 100 cards labeled 0
    stack = deque([0] * 100)
    
    # Process queries
    for _ in range(Q):
        try:
            query_type = int(next(iterator))
            
            if query_type == 1:
                x = int(next(iterator))
                stack.append(x)
            elif query_type == 2:
                top_card = stack.pop()
                print(top_card)
        except StopIteration:
            break

if __name__ == "__main__":
    main()
