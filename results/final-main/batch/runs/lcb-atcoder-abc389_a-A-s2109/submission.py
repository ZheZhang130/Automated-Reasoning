import sys

def main():
    s = sys.stdin.read().strip()
    a = int(s[0])
    b = int(s[2])
    print(a * b)

if __name__ == "__main__":
    main()
