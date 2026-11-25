import sys

def main():
    # Read A and B from standard input
    line = sys.stdin.read().strip()
    if not line:
        return
    parts = line.split()
    A = int(parts[0])
    B = int(parts[1])
    
    # Calculate (A + B)^2
    result = (A + B) ** 2
    
    # Print the result
    print(result)

if __name__ == "__main__":
    main()
