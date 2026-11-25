import sys


def main():
    data = sys.stdin.buffer
    n = int(data.readline())
    sizes = list(map(int, data.read().split()))
    count = 0
    eligible = 0
    for bottom in sizes:
        limit = bottom // 2
        # Every eligible top precedes this bottom, since sizes are positive.
        while sizes[eligible] <= limit:
            eligible += 1
        count += eligible
    print(count)


if __name__ == "__main__":
    main()
