import math
import mpmath

from flask import Flask

app = Flask(__name__)


@app.route('/pi')
def hello():
    with open("pi.txt", "a+") as f:
        f.seek(0)
        number_of_digits = len(f.readline())
        if number_of_digits == 0: # the first ten digits contain a "." that needs to be adjusted for
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
def reset():
    open("pi.txt", "w").truncate()
    return "reset"


if __name__ == "__main__":
    app.run()
