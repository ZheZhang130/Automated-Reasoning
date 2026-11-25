import sys

def main():
    # Read A and B from standard input
    line = sys.stdin.read().strip()
    parts = line.split()
    A = int(parts[0])
    B = int(parts[1])
    
    # Calculate and print the square of A + B
    result = (A + B) ** 2
    print(result)

if __name__ == "__main__":
    main()
