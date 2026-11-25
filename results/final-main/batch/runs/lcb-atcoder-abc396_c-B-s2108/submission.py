import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n, m = data[:2]
    black = sorted(data[2:2 + n], reverse=True)
    white = sorted(data[2 + n:], reverse=True)

    best = black_sum = white_sum = 0
    for i, value in enumerate(black):
        black_sum += value
        # For i+1 black balls, use up to i+1 positive white balls.
        if i < m and white[i] > 0:
            white_sum += white[i]
        best = max(best, black_sum + white_sum)

    print(best)


if __name__ == "__main__":
    main()
