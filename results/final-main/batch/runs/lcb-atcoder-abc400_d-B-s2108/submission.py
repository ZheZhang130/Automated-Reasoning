import sys


def main():
    read = sys.stdin.buffer.readline
    h, w = map(int, read().split())
    stride = w + 4
    board = bytearray((h + 4) * stride)
    # 0: outside or already discovered, 1: road, 2: wall.
    table = bytes.maketrans(b'.#', b'\x01\x02')
    for row in range(2, h + 2):
        left = row * stride + 2
        board[left:left + w] = read().strip().translate(table)

    a, b, c, d = map(int, read().split())
    start = (a + 1) * stride + b + 1
    goal = (c + 1) * stride + d + 1

    # Walking discovers original roads for free. A kick discovers any
    # original wall one or two cells away in its direction. Either wall can
    # be reached immediately after that kick. In a real walk, any revisited
    # broken wall was already reachable when it was first broken, so we do
    # not need to store the set of broken walls for each route.
    #
    # All incoming edges of an original road cost zero, and all incoming
    # edges of an original wall cost one. Thus when processing layers in
    # order, the first discovery of any cell is optimal.
    board[start] = 0
    current = [start]
    kicks = 0
    directions = ((-1, -2), (1, 2), (-stride, -2 * stride), (stride, 2 * stride))
    while current:
        following = []
        pop = current.pop
        add_road = current.append
        add_wall = following.append
        while current:
            pos = pop()
            for step, twice in directions:
                near = pos + step
                kind = board[near]
                if kind == 1:
                    if near == goal:
                        print(kicks)
                        return
                    board[near] = 0
                    add_road(near)
                elif kind == 2:
                    board[near] = 0
                    add_wall(near)

                far = pos + twice
                if board[far] == 2:
                    board[far] = 0
                    add_wall(far)
        current = following
        kicks += 1


if __name__ == '__main__':
    main()
