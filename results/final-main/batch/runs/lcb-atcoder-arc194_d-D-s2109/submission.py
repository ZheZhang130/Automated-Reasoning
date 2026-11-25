import sys
from math import factorial
from collections import Counter

def solve():
    n = int(sys.stdin.readline().strip())
    s = sys.stdin.readline().strip()
    
    # Find primitive components by tracking balance
    # A primitive component starts when balance goes from 0 to 1, and ends when it returns to 0
    balance = 0
    components = []
    for i in range(n):
        if s[i] == '(':
            balance += 1
        else:
            balance -= 1
        if balance == 0:
            # This is the end of a primitive component
            components.append(s[0:i+1])
            # Reset for next component
            # But we need to track the start of each component
            pass
    
    # Actually, let's track start positions
    balance = 0
    start = 0
    components = []
    for i in range(n):
        if s[i] == '(':
            if balance == 0:
                start = i
            balance += 1
        else:
            balance -= 1
        if balance == 0:
            components.append(s[start:i+1])
    
    # Count frequencies of each component
    freq = Counter(components)
    
    total = sum(freq.values())
    ans = factorial(total)
    for count in freq.values():
        ans = ans // factorial(count)
    
    print(ans % 998244353)

solve()
