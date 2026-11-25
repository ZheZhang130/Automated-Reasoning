import sys
from bisect import bisect_left, bisect_right


def main():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(data)
    q = next(data)
    a = [next(data) for _ in range(n)]
    queries = [(next(data), next(data), i) for i in range(q)]
    queries.sort()

    tails = []
    answers = [0] * q
    processed = 0
    for r, x, i in queries:
        while processed < r:
            value = a[processed]
            processed += 1
            pos = bisect_left(tails, value)
            if pos == len(tails):
                tails.append(value)
            else:
                tails[pos] = value
        # tails[k] is the least endpoint of a subsequence of length k+1.
        # In an increasing subsequence the endpoint is also its maximum.
        answers[i] = bisect_right(tails, x)

    sys.stdout.write('\n'.join(map(str, answers)) + '\n')


if __name__ == '__main__':
    main()
