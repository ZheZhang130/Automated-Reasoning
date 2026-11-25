import sys


def count_up_to(n):
    if n < 10:
        return 0
    digits = list(map(int, str(n)))
    length = len(digits)
    first = digits[0]

    # For a fixed leading digit d, every trailing position has d choices.
    total = sum(d ** (size - 1) for size in range(2, length)
                for d in range(1, 10))
    total += sum(d ** (length - 1) for d in range(1, first))

    # With the same leading digit, count by the first differing position.
    for i, digit in enumerate(digits[1:], start=1):
        total += min(digit, first) * first ** (length - i - 1)
        if digit >= first:
            return total

    return total + 1  # n itself is a Snake number.


def main():
    left, right = map(int, sys.stdin.buffer.read().split())
    print(count_up_to(right) - count_up_to(left - 1))


if __name__ == "__main__":
    main()
