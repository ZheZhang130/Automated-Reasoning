import sys

def main():
    # Read A and B from standard input
    line = sys.stdin.read().strip()
    if not line:
        return
    A, B = map(int, line.split())
    # Compute and print the square of (A + B)
    print((A + B) ** 2)

if __name__ == "__main__":
    main()
