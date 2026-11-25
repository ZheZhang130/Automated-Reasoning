import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    p = data[1:n + 1]
    q = data[n + 1:]

    answer = [0] * n
    for target, bib in zip(p, q):
        answer[bib - 1] = q[target - 1]

    print(" ".join(map(str, answer)))


if __name__ == "__main__":
    main()
