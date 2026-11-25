import sys


def main():
    a, b, c = sorted(map(int, sys.stdin.buffer.read().split()))
    print("Yes" if a * b == c else "No")


if __name__ == "__main__":
    main()
