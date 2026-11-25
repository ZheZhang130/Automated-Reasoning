import sys


def main():
    read = sys.stdin.buffer.readline
    h, w = map(int, read().split())
    stride = w + 4
    grid = bytearray((h + 4) * stride)
    table = bytes.maketrans(b'.#', b'\x01\x02')
    for i in range(2, h + 2):
        start = i * stride + 2
        grid[start:start + w] = read().strip().translate(table)

    a, b, c, d = map(int, read().split())
    source = (a + 1) * stride + b + 1
    target = (c + 1) * stride + d + 1

    # A kick can reach either of the first two cells in its direction.
    # If the second cell is a road, reaching it via the first cell
    # costs no more, so paid edges only need to target walls.
    directions = ((1, 2), (-1, -2), (stride, 2 * stride),
                  (-stride, -2 * stride))
    current = [source]
    grid[source] = 0
    kicks = 0
    while current:
        following = []
        # Exhaust all free moves before processing the next kick layer.
        # Roads are discovered only by free edges, and walls only by
        # paid edges, so each cell can be marked on first discovery.
        while current:
            pos = current.pop()
            if pos == target:
                print(kicks)
                return
            for step, double_step in directions:
                near = pos + step
                kind = grid[near]
                if kind == 1:
                    grid[near] = 0
                    current.append(near)
                elif kind == 2:
                    grid[near] = 0
                    following.append(near)
                far = pos + double_step
                if grid[far] == 2:
                    grid[far] = 0
                    following.append(far)
        current = following
        kicks += 1


if __name__ == '__main__':
    main()
