from math import isqrt


def main():
    n = int(input())
    # Odd exponents give twice a square; positive even exponents give
    # four times a square. The two families have different 2-adic parity.
    print(isqrt(n // 2) + isqrt(n // 4))


if __name__ == "__main__":
    main()
