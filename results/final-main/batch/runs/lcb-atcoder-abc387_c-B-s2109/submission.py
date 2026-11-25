import sys


def count_snakes(bound):
    if bound < 10:
        return 0

    digits = list(map(int, str(bound)))
    length = len(digits)
    first = digits[0]

    total = sum(d ** (size - 1)
                for size in range(2, length)
                for d in range(1, 10))
    total += sum(d ** (length - 1) for d in range(1, first))

    for i in range(1, length):
        digit = digits[i]
        total += min(digit, first) * first ** (length - i - 1)
        if digit >= first:
            return total

    return total + 1


def main():
    left, right = map(int, sys.stdin.buffer.read().split())
    print(count_snakes(right) - count_snakes(left - 1))


if __name__ == "__main__":
    main()
