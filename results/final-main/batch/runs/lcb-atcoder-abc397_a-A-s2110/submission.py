import sys

def main():
    line = sys.stdin.read().strip()
    if not line:
        return
    x = float(line)
    
    if x >= 38.0:
        print(1)
    elif x >= 37.5:
        print(2)
    else:
        print(3)

if __name__ == "__main__":
    main()
