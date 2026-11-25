import sys


def main():
    data = sys.stdin.buffer.read().split()
    n, m = map(int, data[:2])
    s = data[2:2 + n]
    t = data[2 + n:]
    limit = n - m + 1

    for a in range(limit):
        for b in range(limit):
            if all(s[a + i][b:b + m] == row for i, row in enumerate(t)):
                print(a + 1, b + 1)
                return


if __name__ == "__main__":
    main()
