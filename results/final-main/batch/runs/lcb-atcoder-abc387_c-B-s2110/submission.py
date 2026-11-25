import sys


def count_up_to(n):
    if n < 10:
        return 0

    digits = [int(c) for c in str(n)]
    length = len(digits)
    leading = digits[0]

    total = sum(d ** k for k in range(1, length - 1) for d in range(1, 10))
    total += sum(d ** (length - 1) for d in range(1, leading))

    for i in range(1, length):
        digit = digits[i]
        total += min(digit, leading) * leading ** (length - i - 1)
        if digit >= leading:
            return total

    return total + 1


def main():
    left, right = map(int, sys.stdin.buffer.read().split())
    print(count_up_to(right) - count_up_to(left - 1))


if __name__ == "__main__":
    main()
