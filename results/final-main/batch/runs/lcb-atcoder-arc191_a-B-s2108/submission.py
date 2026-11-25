import sys


def main():
    read = sys.stdin.buffer.readline
    read()
    s = bytearray(read().strip())
    t = read().strip()
    last = t[-1]
    counts = [0] * 58
    for digit in range(49, 58):
        counts[digit] = t.count(bytes((digit,)))

    best = 57
    used_last = False
    for i, digit in enumerate(s):
        while best >= 49 and counts[best] == 0:
            best -= 1
        if best < 49:
            break
        if best > digit:
            s[i] = best
            counts[best] -= 1
            if best == last:
                used_last = True

    # If an improving replacement used the last digit's value, assign
    # the final operation to one such position. Otherwise, use it on
    # an equal original digit if possible, or sacrifice the last position.
    if not used_last and last not in s:
        s[-1] = last

    sys.stdout.buffer.write(s)
    sys.stdout.buffer.write(b'\n')


if __name__ == '__main__':
    main()
