import sys
from math import isqrt


def main():
    r = int(sys.stdin.buffer.readline())
    diameter_squared = 4 * r * r

    # For column x, the farthest corner has doubled coordinates
    # (2*abs(x)+1, 2*abs(y)+1).
    answer = 2 * r - 1  # The column x = 0.
    for x in range(1, r):
        a = 2 * x + 1
        max_y = (isqrt(diameter_squared - a * a) - 1) // 2
        answer += 2 * (2 * max_y + 1)  # Columns x and -x.
    print(answer)


if __name__ == "__main__":
    main()
