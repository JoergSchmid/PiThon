from database import *
from flask import Flask
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash
from pi_functions import *

app = Flask(__name__)
auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    pw_hash = get_password(create_connection(DB_PATH), username)
    if pw_hash is not None and check_password_hash(pw_hash, password):
        return username


@app.route('/home')
@auth.login_required
def home():
    return f"Welcome home, {auth.current_user()}!"


@app.route('/post', methods=['POST'])
def post():
    data = request.json
    try:
        if 'user' in data:
            user = data['user']
            return f"Hello {user}!"
        if 'index' in data:
            index = int(data['index'])
            return pi_get_digit_at_index(index)
        if 'upto' in data:
            upto = int(data['upto'])
            return pi_get_digits_up_to(upto)
        if 'getfile' in data and (data['getfile'] == "true" or data['getfile']):
            return pi_get_all_from_file()
    except ValueError:
        return "error: invalid key or value in post request"
    return """No valid post request found.
                Valid post requests are:
                'user': 'name', 
                'index': 'int', 
                'upto': 'int', 
                'getfile': 'true'
                """


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


@app.route("/pi_reset")
def pi_reset():
    with open("pi.txt", "w") as f:
        f.truncate()
    return "reset"


if __name__ == "__main__":
    create_user_table()
    app.run()
