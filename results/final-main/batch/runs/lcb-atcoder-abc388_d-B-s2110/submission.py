import sys


def main():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(data)
    expires = [0] * n
    active = 0
    answer = []
    for i, initial in enumerate(data):
        active -= expires[i]
        stones = initial + active
        remaining_years = n - 1 - i
        gifts = min(stones, remaining_years)
        answer.append(str(stones - gifts))

        # This alien gives in each of the next `gifts` years.
        if gifts:
            active += 1
            end = i + gifts + 1
            if end < n:
                expires[end] += 1

    print(" ".join(answer))


if __name__ == "__main__":
    main()
