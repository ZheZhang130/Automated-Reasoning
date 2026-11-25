import sys


def main():
    read = sys.stdin.buffer.readline
    q = int(read())
    stack = [0] * 100
    answers = []

    for _ in range(q):
        query = read().split()
        if query[0] == b"1":
            stack.append(int(query[1]))
        else:
            answers.append(str(stack.pop()))

    print("\n".join(answers))


if __name__ == "__main__":
    main()
