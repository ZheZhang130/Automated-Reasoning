import sys


def main():
    read = sys.stdin.buffer.readline
    n, m = map(int, read().split())
    grid = [read().strip() for _ in range(n)]
    pattern = [read().strip() for _ in range(m)]

    for a in range(n - m + 1):
        for b in range(n - m + 1):
            if all(grid[a + i][b:b + m] == row for i, row in enumerate(pattern)):
                print(a + 1, b + 1)
                return


if __name__ == "__main__":
    main()
