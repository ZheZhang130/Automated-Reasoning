import sys


def main():
    values = list(map(int, sys.stdin.buffer.read().split()))
    n = values[0]
    expires = [0] * (n + 1)
    donors = 0
    result = []

    for i in range(n):
        donors -= expires[i]
        stones = values[i + 1] + donors
        gifts = min(stones, n - 1 - i)
        result.append(str(stones - gifts))
        if gifts:
            donors += 1
            expires[i + gifts + 1] += 1

    sys.stdout.write(" ".join(result) + "\n")


if __name__ == "__main__":
    main()
