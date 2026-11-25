import sys


def main():
    sequence = sys.stdin.readline().strip()
    partner = {')': '(', ']': '[', '>': '<'}
    stack = []
    for bracket in sequence:
        opening = partner.get(bracket)
        if opening is None:
            stack.append(bracket)
        elif not stack or stack.pop() != opening:
            print("No")
            return
    print("No" if stack else "Yes")


if __name__ == "__main__":
    main()
