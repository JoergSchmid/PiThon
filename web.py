from database import *
import mpmath
from flask import Flask, request

app = Flask(__name__)


@app.route('/pi')
def pi():
    user, index = pi_get_user_and_index()

    if user is None:
        if index is None:
            return pi_get_last_ten_digits()
        else:
            return pi_get_digit_at_index(index)
    else:
        conn = create_connection(DB_PATH)
        current_index = get_current_index(conn, user)
        if current_index < 0:
            return "error: user not found"
        pi_string = pi_get_next_ten_digits_from_index(current_index)
        raise_current_index(conn, user, 10)
        return pi_string


def pi_get_user_and_index():
    user = request.args.get("user")
    index = request.args.get("index")
    return user, index


def pi_get_next_ten_digits_from_index(index):
    mpmath.mp.dps = int(index) + 11
    if int(index) == 0:  # Special case for first digit before "."
        return str(mpmath.pi)[-12:-1]
    else:
        return str(mpmath.pi)[-11:-1]


def pi_get_digit_at_index(index):
    try:  # index might be invalid
        if int(index) < 0:
            return "error: index too small"
        if int(index) == 0:  # Special case for first digit before "."
            return "3"
        mpmath.mp.dps = int(index) + 2
        return str(mpmath.pi)[-2]
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
    with open("pi.txt", "w") as f:
        f.truncate()
    return "reset"


if __name__ == "__main__":
    create_user_table()
    app.run()
