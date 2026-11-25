import sys

def main():
    s = sys.stdin.read().strip()
    if len(s) != 3:
        return
    a = int(s[0])
    b = int(s[2])
    print(a * b)

if __name__ == "__main__":
    main()
