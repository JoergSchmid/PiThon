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
        return "Unauthorized. Admin access only.", 403

    conn = create_connection(DB_PATH)

    users = get_all_user_names(conn)
    return users, 200


@app.post('/admin/users')
@auth.login_required
def admin_add_user():
    if not request.is_json:
        return {"error": "Request must be JSON"}, 415

    if auth.current_user() != "joerg":
        return "Unauthorized. Admin access only.", 403

    data = request.get_json()
    conn = create_connection(DB_PATH)

    try:
        if is_user_existing(conn, data["username"]):
            return "User already exists.", 409

        create_user(conn, data["username"], data["password"])
        return data["username"], 201
    except (KeyError, ValueError):
        return "Invalid Request", 400


@app.patch('/admin/users')
@auth.login_required
def admin_change_password():
    if not request.is_json:
        return {"error": "Request must be JSON"}, 415

    if auth.current_user() != "joerg":
        return "Unauthorized. Admin access only.", 403

    username = request.args.get("user")
    if username is None:
        return "No user input found. Please use '?user='", 400

    data = request.get_json()
    conn = create_connection(DB_PATH)

    try:
        if not is_user_existing(conn, username):
            return "User does not exist.", 404

        change_password(conn, username, generate_password_hash(data["password"]))
        return {"username": username, "password": get_password(conn, username)}, 201
    except (KeyError, ValueError):
        return "Invalid Request", 400


@app.delete('/admin/users')
@auth.login_required
def admin_delete_user():
    if auth.current_user() != "joerg":
        return "Unauthorized. Admin access only.", 403

    username = request.args.get("user")
    if username is None:
        return "No user input found. Please use '?user='", 400

    conn = create_connection(DB_PATH)

    if not is_user_existing(conn, username):
        return "User not found.", 404

    delete_user(conn, username)
    return {}, 200


@app.get('/get')
def get():
    try:
        user = request.args.get("user")
        if user is not None:
            return pi_get_next_ten_for_user(user), 200
        index = request.args.get("index")
        if index is not None:
            return pi_get_digit_at_index(int(index)), 200
        upto = request.args.get("upto")
        if upto is not None:
            return pi_get_digits_up_to(int(upto)), 200
        getfile = request.args.get("getfile")
        if getfile is not None and getfile == "true":
            return pi_get_all_from_file(), 200
    except ValueError:
        return {"error": "invalid value"}, 400
    return {"error": "No known request sent"}, 400


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
