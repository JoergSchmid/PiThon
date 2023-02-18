import http
from flask import Flask
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash
from pi_functions import *


app = Flask(__name__)
auth = HTTPBasicAuth()
status = http.HTTPStatus


def innit_app():
    create_user_table()


@auth.verify_password
def verify_password(username, password):
    pw_hash = get_password(create_connection(DB_PATH), username)
    if pw_hash is not None and check_password_hash(pw_hash, password):
        return True
    return False


@app.route('/home')
@auth.login_required
def home():
    return f"Welcome home, {auth.current_user()}!"


@app.get('/admin/users')
@auth.login_required
def admin_get_all_users():
    if auth.current_user() != "joerg":
        return "Unauthorized. Admin access only.", status.FORBIDDEN

    conn = create_connection(DB_PATH)

    users = get_all_user_names(conn)
    return users, status.OK


@app.post('/admin/users')
@auth.login_required
def admin_add_user():
    if not request.is_json:
        return {"error": "Request must be JSON"}, status.UNSUPPORTED_MEDIA_TYPE

    if auth.current_user() != "joerg":
        return "Unauthorized. Admin access only.", status.FORBIDDEN

    data = request.get_json()
    conn = create_connection(DB_PATH)

    try:
        if is_user_existing(conn, data["username"]):
            return "User already exists.", status.CONFLICT

        create_user(conn, data["username"], data["password"])
        return data["username"], status.CREATED
    except (KeyError, ValueError):
        return "Invalid Request", status.BAD_REQUEST


@app.patch('/admin/users')
@auth.login_required
def admin_change_password():
    if not request.is_json:
        return {"error": "Request must be JSON"}, status.UNSUPPORTED_MEDIA_TYPE

    if auth.current_user() != "joerg":
        return "Unauthorized. Admin access only.", status.FORBIDDEN

    username = request.args.get("user")
    if username is None:
        return "No user input found. Please use '?user='", status.BAD_REQUEST

    data = request.get_json()
    conn = create_connection(DB_PATH)

    try:
        if not is_user_existing(conn, username):
            return "User does not exist.", status.NOT_FOUND

        change_password(conn, username, generate_password_hash(data["password"]))
        return {"username": username, "password": "***"}, status.CREATED
    except (KeyError, ValueError):
        return "Invalid Request", status.BAD_REQUEST


@app.delete('/admin/users')
@auth.login_required
def admin_delete_user():
    if auth.current_user() != "joerg":
        return "Unauthorized. Admin access only.", status.FORBIDDEN

    username = request.args.get("user")
    if username is None:
        return "No user input found. Please use '?user='", status.BAD_REQUEST

    conn = create_connection(DB_PATH)

    if not is_user_existing(conn, username):
        return "User not found.", status.NOT_FOUND

    delete_user(conn, username)
    return {}, status.OK


@app.get('/get')
def get():
    try:
        user = request.args.get("user")
        if user is not None:
            return pi_get_next_ten_for_user(user), status.OK
        index = request.args.get("index")
        if index is not None:
            return pi_get_digit_at_index(int(index)), status.OK
        upto = request.args.get("upto")
        if upto is not None:
            return pi_get_digits_up_to(int(upto)), status.OK
        getfile = request.args.get("getfile")
        if getfile is not None and getfile == "true":
            return pi_get_all_from_file(), status.OK
    except ValueError:
        return {"error": "invalid value"}, status.BAD_REQUEST
    return {"error": "No known request sent"}, status.BAD_REQUEST


@app.get('/pi')
def pi():
    user, index = pi_get_user_and_index()

    if user is None:
        if index is None:
            return pi_get_last_ten_digits()
        else:
            return pi_get_digit_at_index(index)
    else:
        return pi_get_next_ten_for_user(user)


@app.delete('/pi')
def pi_delete():
    user, index = pi_get_user_and_index()

    if user is None:
        if index is None:
            pi_reset()
            return {}, status.CREATED
    else:
        reset_current_index(create_connection(DB_PATH), user)
        return {}, status.CREATED


@app.route("/pi_reset")
def pi_reset():
    with open("pi.txt", "w") as f:
        f.truncate()
    return "reset"


if __name__ == "__main__":
    innit_app()
    app.run()
