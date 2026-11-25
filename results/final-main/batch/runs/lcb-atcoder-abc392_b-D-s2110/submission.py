import sys

def main():
    data = sys.stdin.read().split()
    if not data:
        return
    
    n = int(data[0])
    m = int(data[1])
    
    a = set()
    for i in range(m):
        a.add(int(data[2 + i]))
    
    missing = []
    for x in range(1, n + 1):
        if x not in a:
            missing.append(x)
    
    print(len(missing))
    print(" ".join(map(str, missing)))

if __name__ == "__main__":
    main()
