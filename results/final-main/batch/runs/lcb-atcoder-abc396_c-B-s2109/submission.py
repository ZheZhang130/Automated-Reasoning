import sys


def main():
    n, m = map(int, sys.stdin.buffer.readline().split())
    black = sorted(map(int, sys.stdin.buffer.readline().split()), reverse=True)
    white = sorted(map(int, sys.stdin.buffer.readline().split()), reverse=True)

    black_sum = white_sum = best_white = answer = 0
    for i in range(n):
        black_sum += black[i]
        if i < m:
            white_sum += white[i]
            best_white = max(best_white, white_sum)
        answer = max(answer, black_sum + best_white)
    print(answer)


if __name__ == "__main__":
    main()
