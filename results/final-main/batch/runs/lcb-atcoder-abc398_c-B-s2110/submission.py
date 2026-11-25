import sys


def main():
    tokens = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(tokens)
    positions = {}
    for label in range(1, n + 1):
        value = next(tokens)
        positions[value] = -1 if value in positions else label

    largest = 0
    answer = -1
    for value, label in positions.items():
        if label != -1 and value > largest:
            largest = value
            answer = label
    print(answer)


if __name__ == "__main__":
    main()
