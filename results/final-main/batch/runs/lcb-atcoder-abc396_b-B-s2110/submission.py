import sys


def main():
    tokens = iter(map(int, sys.stdin.buffer.read().split()))
    queries = next(tokens)
    stack = [0] * 100
    output = []

    for _ in range(queries):
        if next(tokens) == 1:
            stack.append(next(tokens))
        else:
            output.append(str(stack.pop()))

    print('\n'.join(output))


if __name__ == '__main__':
    main()
