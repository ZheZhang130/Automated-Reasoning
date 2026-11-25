import sys

def main():
    line = sys.stdin.read().strip()
    if not line:
        return
    a, b = map(int, line.split())
    print((a + b) ** 2)

if __name__ == "__main__":
    main()
