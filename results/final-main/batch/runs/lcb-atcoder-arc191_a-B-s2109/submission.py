import sys


def main():
    read = sys.stdin.buffer.readline
    read()
    s = bytearray(read().strip())
    t = read().strip()

    # First maximize the string as if all replacements were optional.
    counts = [t.count(bytes((d,))) for d in range(49, 58)]
    best = 8
    for i, digit in enumerate(s):
        while best >= 0 and counts[best] == 0:
            best -= 1
        if best <= 0:
            break
        if best + 49 > digit:
            s[i] = best + 49
            counts[best] -= 1

    # The last operation must survive. If its digit occurs in the
    # relaxed optimum, assign that operation to one such position.
    # Otherwise we can preserve the optimal prefix and change its end.
    last = t[-1]
    if last not in s:
        s[-1] = last

    sys.stdout.buffer.write(s + b'\n')


if __name__ == '__main__':
    main()
