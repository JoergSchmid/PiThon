import math
import mpmath

from flask import Flask

app = Flask(__name__)


@app.route('/pi')
def hello():
    line = ""
    with open("pi.txt", "r") as f:
        line = f.readline()
        if line == "":
            line = "10"
        else:
            line = str(int(line) + 10)

    open("pi.txt", "w").write(line)
    mpmath.mp.dps = int(line)
    last_ten = str(4*mpmath.atan(1))
    last_ten = last_ten[len(last_ten) - 10 : len(last_ten)]
    return last_ten


if __name__ == "__main__":
    app.run()
