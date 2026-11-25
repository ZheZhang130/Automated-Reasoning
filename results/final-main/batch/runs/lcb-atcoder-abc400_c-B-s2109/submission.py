from math import isqrt


def main():
    n = int(input())
    # Odd exponents give 2*k^2, and positive even exponents give 4*k^2.
    # The two families are disjoint by the parity of the power of 2.
    print(isqrt(n // 2) + isqrt(n // 4))


if __name__ == "__main__":
    main()
