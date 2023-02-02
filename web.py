import math
import mpmath

from flask import Flask

app = Flask(__name__)


@app.route('/pi')
def hello():
    digit_index = ""
    with open("pi.txt", "a+") as f:
        f.seek(0)
        digit_index = f.readline()
        if digit_index == "":
            digit_index = "9"
        else:
            digit_index = str(int(digit_index) + 10)

    with open("pi.txt", "w") as f:
        f.write(digit_index)
    mpmath.mp.dps = int(digit_index) + 1
    last_ten = str(mpmath.pi)
    last_ten = last_ten[-11:-1]
    return last_ten


if __name__ == "__main__":
    app.run()
