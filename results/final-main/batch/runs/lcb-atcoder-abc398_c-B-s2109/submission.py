import sys


def main():
    tokens = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(tokens)
    labels = {}
    for label in range(1, n + 1):
        value = next(tokens)
        labels[value] = 0 if value in labels else label

    best = 0
    answer = -1
    for value, label in labels.items():
        if label and value > best:
            best = value
            answer = label
    print(answer)


if __name__ == "__main__":
    main()
