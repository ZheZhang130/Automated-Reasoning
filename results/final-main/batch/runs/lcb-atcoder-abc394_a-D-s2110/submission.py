import sys

def main():
    s = sys.stdin.read().strip()
    result = ''.join(c for c in s if c == '2')
    print(result)

if __name__ == "__main__":
    main()
