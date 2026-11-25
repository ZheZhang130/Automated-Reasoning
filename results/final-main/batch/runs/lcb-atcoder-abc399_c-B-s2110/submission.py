import sys


def main():
    readline = sys.stdin.buffer.readline
    n, m = map(int, readline().split())
    parent = list(range(n + 1))
    size = [1] * (n + 1)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    removed = 0
    for _ in range(m):
        u, v = map(int, readline().split())
        a, b = find(u), find(v)
        if a == b:
            removed += 1
        else:
            if size[a] < size[b]:
                a, b = b, a
            parent[b] = a
            size[a] += size[b]
    print(removed)


if __name__ == "__main__":
    main()
