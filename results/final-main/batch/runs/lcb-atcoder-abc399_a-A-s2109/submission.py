def main():
    n = int(input())
    s = input()
    t = input()
    
    hamming_distance = 0
    for i in range(n):
        if s[i] != t[i]:
            hamming_distance += 1
    
    print(hamming_distance)

if __name__ == "__main__":
    main()
