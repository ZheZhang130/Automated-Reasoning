def main():
    s = input().strip()
    insertions = 0
    expected = 'i'
    for char in s:
        if char != expected:
            insertions += 1
        expected = 'o' if char == 'i' else 'i'
    if expected == 'o':
        insertions += 1
    print(insertions)


if __name__ == '__main__':
    main()
