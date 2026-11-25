import sys


def main():
    read = sys.stdin.buffer.readline
    h, w = map(int, read().split())
    stride = w + 2
    # 0: border or reached at the current/earlier level
    # 1/2: unseen road/wall; 3/4: road/wall queued by a kick
    cells = bytearray((h + 2) * stride)
    table = bytes.maketrans(b'.#', b'\x01\x02')
    for row in range(1, h + 1):
        left = row * stride + 1
        cells[left:left + w] = read().strip().translate(table)

    a, b, c, d = map(int, read().split())
    start = a * stride + b
    goal = c * stride + d
    directions = (-stride, stride, -1, 1)

    # Each layer is seeded by kick destinations; flood its free road moves
    # before moving to the next layer.
    seeds = [start]
    kicks = 0
    while seeds:
        following = []
        stack = []
        for seed in seeds:
            if not cells[seed]:
                continue
            cells[seed] = 0
            stack.append(seed)
            while stack:
                pos = stack.pop()
                if pos == goal:
                    print(kicks)
                    return
                for step in directions:
                    near = pos + step
                    state = cells[near]
                    if state == 1 or state == 3:
                        cells[near] = 0
                        stack.append(near)
                    elif state == 2 or state == 4:
                        if state == 2:
                            cells[near] = 4
                            following.append(near)
                        # If the neighbor is already reachable for free, it
                        # can handle the second cell itself at no extra cost.
                        far = near + step
                        state = cells[far]
                        if state == 1 or state == 2:
                            cells[far] = state + 2
                            following.append(far)
        seeds = following
        kicks += 1


if __name__ == "__main__":
    main()
