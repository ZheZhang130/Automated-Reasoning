import sys


def main():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(data)
    two_back = 0
    one_back = next(data)

    # Between surviving pushes, the operations form balanced blocks.
    # Each such block can be replaced by adjacent push-pop pairs.
    for _ in range(1, n):
        value = next(data)
        two_back, one_back = one_back, max(one_back + value, two_back)

    print(one_back)


if __name__ == "__main__":
    main()
