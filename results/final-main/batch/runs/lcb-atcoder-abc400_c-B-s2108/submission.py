from math import isqrt


def main():
    n = int(input())
    # Odd exponents give 2 times a square; positive even exponents
    # give 4 times a square. Their powers of 2 have opposite parity.
    print(isqrt(n // 2) + isqrt(n // 4))


if __name__ == "__main__":
    main()
