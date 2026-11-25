def main():
    n = int(input())
    for row in range(n):
        print(''.join(
            '#.'[min(row, col, n - 1 - row, n - 1 - col) % 2]
            for col in range(n)
        ))


if __name__ == '__main__':
    main()
