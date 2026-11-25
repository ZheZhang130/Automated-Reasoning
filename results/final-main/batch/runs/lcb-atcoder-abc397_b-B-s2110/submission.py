def main():
    s = input().strip()
    expected = 'i'
    insertions = 0
    for c in s:
        if c != expected:
            insertions += 1
        expected = 'o' if c == 'i' else 'i'
    if expected == 'o':
        insertions += 1
    print(insertions)


if __name__ == '__main__':
    main()
