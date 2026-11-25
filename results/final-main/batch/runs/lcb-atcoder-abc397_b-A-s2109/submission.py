import sys

def solve():
    s = sys.stdin.read().strip()
    n = len(s)
    i_count = s.count('i')
    o_count = s.count('o')
    
    # We need equal number of i and o, and total length even
    # Current length is n
    # We need to add characters to make i_count == o_count
    # And total length even (which is automatically satisfied if i_count == o_count)
    
    diff = abs(i_count - o_count)
    print(diff)

if __name__ == "__main__":
    solve()
