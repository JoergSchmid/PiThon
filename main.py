# This is a sample Python script.

# Press Umschalt+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

def main():
    foo_bar(21)
    x = 100
    print(f"Hi{x}")


def foo_bar(end):
    for i in range(1, end):
        s = ""
        if i % 2 == 0:
            s = "Foo"
        if i % 3 == 0:
            s += "Fizz"
        if i % 5 == 0:
            s += "Buzz"
        if i % 7 == 0:
            s += "Bar"

        if s == "":
            print(i)
        else:
            print(s)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    x = 5
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
