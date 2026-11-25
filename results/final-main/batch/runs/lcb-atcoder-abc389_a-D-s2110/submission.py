import sys

def main():
    s = sys.stdin.read().strip()
    if len(s) != 3:
        return
    first_digit = int(s[0])
    third_digit = int(s[2])
    print(first_digit * third_digit)

if __name__ == "__main__":
    main()
