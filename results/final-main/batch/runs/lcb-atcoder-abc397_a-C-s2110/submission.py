import sys

def main():
    x_str = sys.stdin.read().strip()
    x = float(x_str)
    
    if x >= 38.0:
        print(1)
    elif x >= 37.5:
        print(2)
    else:
        print(3)

if __name__ == "__main__":
    main()
