import sys
from bisect import bisect_left, bisect_right


def main():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    n, q = next(data), next(data)
    sequence = [next(data) for _ in range(n)]
    queries = [(next(data), i, next(data)) for i in range(q)]
    queries.sort()

    tails = []
    answers = [0] * q
    processed = 0
    for r, i, x in queries:
        while processed < r:
            value = sequence[processed]
            j = bisect_left(tails, value)
            if j == len(tails):
                tails.append(value)
            else:
                tails[j] = value
            processed += 1

        # Each tail is the smallest possible last value for its length.
        # A strictly increasing subsequence is bounded by x iff its last value is.
        answers[i] = bisect_right(tails, x)

    sys.stdout.write('\n'.join(map(str, answers)) + '\n')


if __name__ == '__main__':
    main()
