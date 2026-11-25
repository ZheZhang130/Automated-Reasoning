import sys


def main():
    n = int(sys.stdin.buffer.readline())
    p = list(map(int, sys.stdin.buffer.readline().split()))
    q = list(map(int, sys.stdin.buffer.readline().split()))

    answer = [0] * n
    for target, bib in zip(p, q):
        answer[bib - 1] = q[target - 1]

    print(" ".join(map(str, answer)))


if __name__ == "__main__":
    main()
