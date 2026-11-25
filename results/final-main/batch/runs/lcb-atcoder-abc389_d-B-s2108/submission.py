import sys
from math import isqrt


def main():
    radius = int(sys.stdin.buffer.readline())
    limit = 4 * radius * radius

    # At column x, the farthest corner has doubled coordinates
    # 2*abs(x)+1 and 2*abs(y)+1.
    max_y = (isqrt(limit - 1) - 1) // 2
    answer = 2 * max_y + 1

    for x in range(3, 2 * radius, 2):
        max_y = (isqrt(limit - x * x) - 1) // 2
        answer += 2 * (2 * max_y + 1)

    print(answer)


if __name__ == "__main__":
    main()
