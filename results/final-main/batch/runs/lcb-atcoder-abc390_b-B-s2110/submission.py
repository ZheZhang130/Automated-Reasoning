import sys


def main():
    n, *a = map(int, sys.stdin.buffer.read().split())
    is_geometric = all(a[i] * a[0] == a[i - 1] * a[1] for i in range(2, n))
    print("Yes" if is_geometric else "No")


if __name__ == "__main__":
    main()
