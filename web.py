import mpmath
from flask import Flask, request

app = Flask(__name__)


@app.route('/pi')
def pi():
    index = request.args.get("index")
    if index is None:
        return pi_get_last_ten_digits()
    else:
        return pi_get_digit_at_index(index)


def pi_get_digit_at_index(index):
    try:  # index might be invalid
        if int(index) < 0:
            return "error: index too small"
        if int(index) == 0:  # Special case for first digit before "."
            return "3"
        mpmath.mp.dps = int(index) + 2
        return str(mpmath.pi)[-2:-1]
    except ValueError:
        return "error: invalid index"


def pi_get_last_ten_digits():
    with open("pi.txt", "a+") as f:
        f.seek(0)
        number_of_digits = len(f.readline())
        if number_of_digits == 0:  # the first ten digits contain a "." that needs to be adjusted for
            number_of_digits = 1
        mpmath.mp.dps = number_of_digits + 10
        pi = str(mpmath.pi)
        f.seek(0)
        f.truncate()
        f.write(pi)
        if number_of_digits == 1:
            return pi[-12:-1]
        return pi[-12:-2]


@app.route("/pi_reset")
def pi_reset():
    open("pi.txt", "w").truncate()
    return "reset"


if __name__ == "__main__":
    app.run()
