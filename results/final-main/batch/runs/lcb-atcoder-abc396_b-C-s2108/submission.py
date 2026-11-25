import sys

def main():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    try:
        Q = int(next(iterator))
    except StopIteration:
        return
    
    # Initialize stack with 100 cards labeled 0
    stack = [0] * 100
    
    # Process queries
    for _ in range(Q):
        try:
            c = int(next(iterator))
            if c == 1:
                x = int(next(iterator))
                stack.append(x)
            elif c == 2:
                top = stack.pop()
                print(top)
        except StopIteration:
            break

if __name__ == "__main__":
    main()
