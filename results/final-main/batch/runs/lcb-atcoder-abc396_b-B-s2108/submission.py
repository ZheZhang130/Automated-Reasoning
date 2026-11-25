import sys


def main():
    tokens = iter(map(int, sys.stdin.buffer.read().split()))
    q = next(tokens)
    stack = [0] * 100
    answers = []

    for _ in range(q):
        if next(tokens) == 1:
            stack.append(next(tokens))
        else:
            answers.append(str(stack.pop()))

    print("\n".join(answers))


if __name__ == "__main__":
    main()
