import sys


def main():
    read = sys.stdin.buffer.readline
    n = int(read())
    p = list(map(int, read().split()))
    q = list(map(int, read().split()))

    answer = [0] * n
    for target, bib in zip(p, q):
        answer[bib - 1] = q[target - 1]

    print(" ".join(map(str, answer)))


if __name__ == "__main__":
    main()
