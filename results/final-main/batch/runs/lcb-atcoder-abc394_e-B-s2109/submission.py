import sys


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    rows = data[1:]
    bits = [1 << i for i in range(n)]
    full = (1 << n) - 1
    unseen = [full ^ bit for bit in bits]
    dist = [[-1] * n for _ in range(n)]
    incoming = [[] for _ in range(n)]
    outgoing = [[0] * 26 for _ in range(n)]
    queue = [(i, i) for i in range(n)]
    for i, row in enumerate(rows):
        dist[i][i] = 0
        masks = outgoing[i]
        for j, ch in enumerate(row):
            if ch == 45:
                continue
            c = ch - 97
            incoming[j].append((i, c))
            masks[c] |= bits[j]
            if i != j:
                dist[i][j] = 1
                unseen[i] ^= bits[j]
                queue.append((i, j))

    total = n * n
    for u, v in queue:
        if len(queue) == total:
            break
        next_dist = dist[u][v] + 2
        masks = outgoing[v]
        for x, c in incoming[u]:
            new = unseen[x] & masks[c]
            if not new:
                continue
            unseen[x] ^= new
            row = dist[x]
            while new:
                bit = new & -new
                new ^= bit
                y = bit.bit_length() - 1
                row[y] = next_dist
                queue.append((x, y))

    sys.stdout.write('\n'.join(' '.join(map(str, row)) for row in dist) + '\n')


if __name__ == '__main__':
    main()
