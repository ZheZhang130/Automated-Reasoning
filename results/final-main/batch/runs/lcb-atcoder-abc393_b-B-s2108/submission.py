def main():
    s = input().strip()
    n = len(s)
    answer = 0

    for j, char in enumerate(s):
        if char == 'B':
            for d in range(1, min(j, n - 1 - j) + 1):
                if s[j - d] == 'A' and s[j + d] == 'C':
                    answer += 1

    print(answer)


if __name__ == '__main__':
    main()
