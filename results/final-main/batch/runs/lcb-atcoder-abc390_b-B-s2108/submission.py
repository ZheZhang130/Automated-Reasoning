import sys


def main():
    n, *a = map(int, sys.stdin.buffer.read().split())
    first, second = a[:2]
    is_geometric = all(
        first * a[i] == second * a[i - 1] for i in range(2, n)
    )
    print("Yes" if is_geometric else "No")


if __name__ == "__main__":
    main()
