import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    expires = [0] * (n + 1)
    active = 0
    answer = []

    for i in range(n):
        active -= expires[i]
        stones = data[i + 1] + active
        gifts = min(stones, n - i - 1)
        answer.append(str(stones - gifts))
        if gifts:
            # This alien gives at ceremonies i+1 through i+gifts.
            active += 1
            expires[i + gifts + 1] += 1

    sys.stdout.write(" ".join(answer) + "\n")


if __name__ == "__main__":
    main()
