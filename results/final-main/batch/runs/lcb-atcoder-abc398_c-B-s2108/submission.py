import sys


def main():
    tokens = iter(sys.stdin.buffer.read().split())
    n = int(next(tokens))
    labels = {}
    for label in range(1, n + 1):
        value = int(next(tokens))
        if value in labels:
            labels[value] = -1
        else:
            labels[value] = label

    largest = 0
    answer = -1
    for value, label in labels.items():
        if label != -1 and value > largest:
            largest = value
            answer = label
    print(answer)


if __name__ == "__main__":
    main()
