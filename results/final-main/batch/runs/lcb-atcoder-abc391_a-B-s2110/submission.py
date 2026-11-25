def main():
    direction = input().strip()
    print(direction.translate(str.maketrans("NSEW", "SNWE")))


if __name__ == "__main__":
    main()
