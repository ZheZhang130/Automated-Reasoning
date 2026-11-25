def main():
    direction = input().strip()
    print(direction.translate(str.maketrans("NEWS", "SWEN")))


if __name__ == "__main__":
    main()
