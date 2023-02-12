import http
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
            return pi_get_next_ten_for_user(user)
        if 'index' in data:
            index = int(data['index'])
            return pi_get_digit_at_index(index)
        if 'upto' in data:
            upto = int(data['upto'])
            return pi_get_digits_up_to(upto)
        if 'getfile' in data and data['getfile'] == "true":
            return pi_get_all_from_file()
    except ValueError:
        return "Error during option parsing", http.HTTPStatus(500)
    return """No valid post request found.
                Valid post requests are:
                'user': 'name', 
                'index': 'int', 
                'upto': 'int', 
                'getfile': 'true'
                """, http.HTTPStatus(400)


@app.route('/pi', methods=['GET', 'DELETE'])
def pi():
    user, index = pi_get_user_and_index()
    is_delete_request = str(request.method) == "DELETE"

    if user is None:
        if index is None:
            if is_delete_request:
                return pi_reset()
            return pi_get_last_ten_digits()
        else:
            return pi_get_digit_at_index(index)
    else:
        if is_delete_request:
            reset_current_index(create_connection(DB_PATH), user)
            return f"reset {user}"
        return pi_get_next_ten_for_user(user)


@app.route("/pi_reset")
def pi_reset():
    with open("pi.txt", "w") as f:
        f.truncate()
    return "reset"


if __name__ == "__main__":
    create_user_table()
    app.run()
