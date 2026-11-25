import sys


def main():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(data)
    sizes = list(data)
    top = 0
    answer = 0
    for bottom in sizes:
        limit = bottom // 2
        while top < n and sizes[top] <= limit:
            top += 1
        answer += top
    print(answer)


if __name__ == "__main__":
    main()
