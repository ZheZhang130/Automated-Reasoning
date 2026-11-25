import sys


def main():
    _, s, t = sys.stdin.buffer.read().split()
    print(sum(a != b for a, b in zip(s, t)))


if __name__ == "__main__":
    main()
