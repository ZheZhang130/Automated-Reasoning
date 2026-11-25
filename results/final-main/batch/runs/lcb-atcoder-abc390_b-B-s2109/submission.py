import sys


def main():
    n, *a = map(int, sys.stdin.buffer.read().split())
    first, second = a[:2]
    is_geometric = all(a[i] * first == a[i - 1] * second for i in range(2, n))
    print("Yes" if is_geometric else "No")


if __name__ == "__main__":
    main()
