import sys

def main():
    input = sys.stdin.read
    data = input().split()
    iterator = iter(data)
    
    Q = int(next(iterator))
    
    # Initialize stack with 100 cards labeled 0
    stack = [0] * 100
    
    results = []
    
    for _ in range(Q):
        query_type = int(next(iterator))
        if query_type == 1:
            x = int(next(iterator))
            stack.append(x)
        else:
            top = stack.pop()
            results.append(str(top))
    
    print('\n'.join(results))

if __name__ == "__main__":
    main()
