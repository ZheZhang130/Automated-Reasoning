import sys

MOD = 998244353


def main():
    tokens = sys.stdin.buffer.read().split()
    if not tokens:
        return
    s = tokens[1]
    pairs = len(s) // 2

    fact = [1] * (pairs + 1)
    inv_fact = [1] * (pairs + 1)
    for i in range(1, pairs + 1):
        fact[i] = fact[i - 1] * i % MOD
    inv_fact[pairs] = pow(fact[pairs], MOD - 2, MOD)
    for i in range(pairs, 0, -1):
        inv_fact[i - 1] = inv_fact[i] * i % MOD

    # The outermost list is the child list of a virtual root.
    stack = [[]]
    types = {}
    answer = 1

    def finish(children):
        nonlocal answer
        children.sort()
        answer = answer * fact[len(children)] % MOD
        i = 0
        while i < len(children):
            j = i + 1
            while j < len(children) and children[j] == children[i]:
                j += 1
            answer = answer * inv_fact[j - i] % MOD
            i = j

    # A balanced interval consists of consecutive siblings. Mirroring
    # two siblings together, then mirroring each separately, swaps them.
    # Thus only the unordered subtree types constrain child permutations.
    for c in s:
        if c == 40:
            stack.append([])
        else:
            children = stack.pop()
            finish(children)
            key = tuple(children)
            type_id = types.setdefault(key, len(types))
            stack[-1].append(type_id)

    finish(stack[0])
    print(answer)


if __name__ == "__main__":
    main()
