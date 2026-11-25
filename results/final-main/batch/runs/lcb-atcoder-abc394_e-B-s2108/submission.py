import sys
from collections import deque


def main():
    input = sys.stdin.buffer.readline
    n = int(input())
    bits = [1 << i for i in range(n)]
    unseen = [(1 << n) - 1] * n
    incoming = [[] for _ in range(n)]
    outgoing = [[0] * 26 for _ in range(n)]
    dist = [[-1] * n for _ in range(n)]
    queue = deque()

    for i in range(n):
        dist[i][i] = 0
        unseen[i] ^= bits[i]
        queue.append((i, i, 0))

    for i in range(n):
        for j, ch in enumerate(input().strip()):
            if ch == 45:
                continue
            c = ch - 97
            incoming[j].append((i, c))
            outgoing[i][c] |= bits[j]
            if i != j:
                dist[i][j] = 1
                unseen[i] ^= bits[j]
                queue.append((i, j, 1))

    # Wrap each known palindrome in two edges with the same label.
    # The initial distances are 0 and 1, and every extension adds 2,
    # so the queue processes pairs in nondecreasing distance order.
    while queue:
        left, right, length = queue.popleft()
        next_length = length + 2
        masks = outgoing[right]
        for start, c in incoming[left]:
            ends = masks[c] & unseen[start]
            if not ends:
                continue
            unseen[start] ^= ends
            row = dist[start]
            while ends:
                bit = ends & -ends
                ends ^= bit
                end = bit.bit_length() - 1
                row[end] = next_length
                queue.append((start, end, next_length))

    sys.stdout.write('\n'.join(' '.join(map(str, row)) for row in dist) + '\n')


if __name__ == '__main__':
    main()
