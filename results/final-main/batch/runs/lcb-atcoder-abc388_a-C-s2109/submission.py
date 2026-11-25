import sys

def main():
    s = sys.stdin.read().strip()
    if s:
        print(s[0] + "UPC")

if __name__ == "__main__":
    main()
