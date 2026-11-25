import sys

def main():
    s = sys.stdin.read().strip()
    if not s:
        return
    first_char = s[0]
    print(first_char + "UPC")

if __name__ == "__main__":
    main()
