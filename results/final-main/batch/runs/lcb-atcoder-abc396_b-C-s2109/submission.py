import sys

def main():
    input = sys.stdin.read
    data = input().split()
    iterator = iter(data)
    
    Q = int(next(iterator))
    
    # Initial stack: 100 cards labeled 0
    stack = [0] * 100
    
    # Process queries
    for _ in range(Q):
        query_type = int(next(iterator))
        if query_type == 1:
            x = int(next(iterator))
            stack.append(x)
        else:
            # Type 2: remove top and output
            top = stack.pop()
            print(top)

if __name__ == "__main__":
    main()
