import sys


def main():
    n, m, *values = map(int, sys.stdin.buffer.read().split())
    black = sorted(values[:n], reverse=True)
    white = sorted(values[n:], reverse=True)

    black_count = 0
    total = 0
    while black_count < n and black[black_count] > 0:
        total += black[black_count]
        black_count += 1

    answer = total
    for i in range(min(n, m)):
        if white[i] <= 0:
            break
        total += white[i]
        if i >= black_count:
            total += black[i]
        answer = max(answer, total)

    print(answer)


if __name__ == "__main__":
    main()
