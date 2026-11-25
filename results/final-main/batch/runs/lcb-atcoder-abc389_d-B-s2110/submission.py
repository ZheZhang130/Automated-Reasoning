import sys
from math import isqrt


def main():
    r = int(sys.stdin.buffer.readline())
    limit = 4 * r * r
    quadrant = 0
    for x in range(3, 2 * r, 2):
        quadrant += (isqrt(limit - x * x) - 1) // 2
    print(1 + 4 * (r - 1 + quadrant))


if __name__ == "__main__":
    main()
