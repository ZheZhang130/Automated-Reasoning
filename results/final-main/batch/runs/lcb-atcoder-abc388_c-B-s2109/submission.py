import sys


def main():
    values = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(values)
    sizes = list(values)
    eligible = 0
    answer = 0
    for bottom in sizes:
        limit = bottom // 2
        while sizes[eligible] <= limit:
            eligible += 1
        answer += eligible
    print(answer)


if __name__ == "__main__":
    main()
