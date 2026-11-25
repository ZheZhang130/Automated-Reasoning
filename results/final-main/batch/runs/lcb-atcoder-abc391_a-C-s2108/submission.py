import sys

def opposite_direction(d):
    # Map each character to its opposite
    mapping = {
        'N': 'S',
        'S': 'N',
        'E': 'W',
        'W': 'E',
    }
    result = []
    for char in d:
        result.append(mapping[char])
    return ''.join(result)

def main():
    d = sys.stdin.read().strip()
    print(opposite_direction(d))

if __name__ == "__main__":
    main()
