import sys


def main():
    sequence = sys.stdin.readline().strip()
    closing = {'(': ')', '[': ']', '<': '>'}
    stack = []
    for char in sequence:
        if char in closing:
            stack.append(closing[char])
        elif not stack or stack.pop() != char:
            print("No")
            return
    print("No" if stack else "Yes")


if __name__ == "__main__":
    main()
