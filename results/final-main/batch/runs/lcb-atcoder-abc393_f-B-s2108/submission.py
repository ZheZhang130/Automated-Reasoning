import sys
from bisect import bisect_left, bisect_right


def main():
    readline = sys.stdin.buffer.readline
    n, q = map(int, readline().split())
    a = list(map(int, readline().split()))
    queries = []
    for i in range(q):
        r, x = map(int, readline().split())
        queries.append((r, x, i))
    queries.sort()

    # tails[k] is the smallest last value of a length-(k+1) subsequence.
    tails = []
    answers = [0] * q
    processed = 0
    for r, x, i in queries:
        while processed < r:
            value = a[processed]
            j = bisect_left(tails, value)
            if j == len(tails):
                tails.append(value)
            else:
                tails[j] = value
            processed += 1
        # In an increasing subsequence, bounding the last value bounds all values.
        answers[i] = bisect_right(tails, x)

    sys.stdout.write("\n".join(map(str, answers)) + "\n")


if __name__ == "__main__":
    main()
