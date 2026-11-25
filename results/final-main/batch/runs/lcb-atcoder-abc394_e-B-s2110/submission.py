import sys
from collections import deque


def main():
    read = sys.stdin.buffer.readline
    n = int(read())
    graph = [read().strip() for _ in range(n)]

    incoming = [[] for _ in range(n)]
    outgoing = [[0] * 26 for _ in range(n)]
    dist = [[-1] * n for _ in range(n)]
    bits = [1 << i for i in range(n)]
    unseen = [(1 << n) - 1] * n
    queue = deque()

    # Empty palindromes, followed by all one-edge palindromes.
    for i in range(n):
        dist[i][i] = 0
        unseen[i] ^= bits[i]
        queue.append((i, i))

    for i, row in enumerate(graph):
        for j, label in enumerate(row):
            if label == 45:
                continue
            c = label - 97
            incoming[j].append((i, c))
            outgoing[i][c] |= bits[j]
            if i != j:
                dist[i][j] = 1
                unseen[i] ^= bits[j]
                queue.append((i, j))

    # Wrap each known palindrome with two edges of the same label.
    # The two starting distances are consecutive, so the queue stays
    # in nondecreasing distance order when every transition adds two.
    while queue:
        u, v = queue.popleft()
        length = dist[u][v] + 2
        right = outgoing[v]
        for i, c in incoming[u]:
            targets = unseen[i] & right[c]
            if targets:
                unseen[i] ^= targets
                row = dist[i]
                while targets:
                    bit = targets & -targets
                    targets ^= bit
                    j = bit.bit_length() - 1
                    row[j] = length
                    queue.append((i, j))

    sys.stdout.write('\n'.join(' '.join(map(str, row)) for row in dist) + '\n')


if __name__ == '__main__':
    main()
