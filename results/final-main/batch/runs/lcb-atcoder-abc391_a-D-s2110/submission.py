def opposite_direction(d):
    opposites = {
        'N': 'S',
        'S': 'N',
        'E': 'W',
        'W': 'E',
        'NE': 'SW',
        'SW': 'NE',
        'NW': 'SE',
        'SE': 'NW'
    }
    return opposites[d]

if __name__ == "__main__":
    d = input().strip()
    print(opposite_direction(d))
