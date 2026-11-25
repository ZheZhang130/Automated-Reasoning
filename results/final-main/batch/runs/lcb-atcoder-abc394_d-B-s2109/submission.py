import sys


def main():
    s = sys.stdin.buffer.readline().strip()
    opening = {ord('('): ord(')'), ord('['): ord(']'), ord('<'): ord('>')}
    stack = []
    for ch in s:
        if ch in opening:
            stack.append(opening[ch])
        elif not stack or stack.pop() != ch:
            print("No")
            return
    print("No" if stack else "Yes")


if __name__ == "__main__":
    main()
