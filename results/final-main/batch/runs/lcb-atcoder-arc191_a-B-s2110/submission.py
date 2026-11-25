import sys

def main():
    read = sys.stdin.buffer.readline
    n, _ = map(int, read().split())
    s = bytearray(read().strip())
    t = read().strip()
    mandatory = t[-1]
    remaining = [0] * 58
    for digit in range(49, 58):
        remaining[digit] = t.count(bytes((digit,)))

    highest = 57
    pending = True
    can_place_without_change = False
    for i in range(n - 1):
        current = s[i]
        while highest >= 49 and not remaining[highest]:
            highest -= 1
        if highest > current:
            s[i] = highest
            remaining[highest] -= 1
            if highest == mandatory:
                pending = False
        elif current == mandatory:
            can_place_without_change = True

    if pending and not can_place_without_change:
        s[-1] = mandatory
    else:
        while highest >= 49 and not remaining[highest]:
            highest -= 1
        if highest > s[-1]:
            s[-1] = highest

    sys.stdout.buffer.write(s + b'\n')

if __name__ == '__main__':
    main()
