import http
from flask import Flask, request, send_file
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash
from database import *
from irrational_digits import Pi, E, Sqrt2
from pathlib import Path

status = http.HTTPStatus
CONFIG_DB_PATH = "DB_PATH"
CONFIG_PI_TXT_PATH = "PI_TXT_PATH"
CONFIG_E_TXT_PATH = "E_TXT_PATH"
CONFIG_SQRT2_TXT_PATH = "SQRT2_TXT_PATH"


def create_app(storage_folder="./db/"):
    """
    Formatted according to https://flask.palletsprojects.com/en/2.2.x/tutorial/factory/
    :param storage_folder: folder the database should use
    :return: app
    """
    app = Flask(__name__)
    app.config[CONFIG_DB_PATH] = Path(storage_folder) / "pi.db"
    app.config[CONFIG_PI_TXT_PATH] = Path(storage_folder) / "pi.txt"
    app.config[CONFIG_E_TXT_PATH] = Path(storage_folder) / "e.txt"
    app.config[CONFIG_SQRT2_TXT_PATH] = Path(storage_folder) / "sqrt2.txt"

    auth = HTTPBasicAuth()
    i_pi = Pi()
    i_e = E()
    i_sqrt2 = Sqrt2()

    create_user_table(app.config[CONFIG_DB_PATH])

    def is_admin(user):
        return user == TEST_USER_ADMIN[0]

    @auth.verify_password
    def verify_password(username, password):
        pw_hash = get_password(create_connection(app.config[CONFIG_DB_PATH]), username)
        if pw_hash is not None and check_password_hash(pw_hash, password):
            return True
        return False

    @app.route('/home')
    @auth.login_required
    def home():
        return f"Welcome home, {auth.current_user()}!"

    @app.get('/digits/<file>')
    def download_file(file):
        path = f"C:/gitroot/PiThon/db/{file}.txt"
        if os.path.exists(path):
            return send_file(path, as_attachment=True), status.OK
        return "File not found", status.NOT_FOUND

    @app.get('/admin/users')
    @auth.login_required
    def admin_get_all_users():
        if not is_admin(auth.current_user()):
            return "Unauthorized. Admin access only.", status.FORBIDDEN

        conn = create_connection(app.config[CONFIG_DB_PATH])

        users = get_all_user_names(conn)
        return users, status.OK

    @app.post('/admin/users')
    @auth.login_required
    def admin_add_user():
        if not request.is_json:
            return {"error": "Request must be JSON"}, status.UNSUPPORTED_MEDIA_TYPE

        if not is_admin(auth.current_user()):
            return "Unauthorized. Admin access only.", status.FORBIDDEN

        data = request.get_json()
        conn = create_connection(app.config[CONFIG_DB_PATH])

        try:
            if is_user_existing(conn, data["username"]):
                return "User already exists.", status.CONFLICT

            if data["username"] in FORBIDDEN_NAMES:
                return "Illegal name.", status.CONFLICT

            create_user(conn, data["username"], data["password"])
            return data["username"], status.CREATED
        except (KeyError, ValueError):
            return "Invalid Request", status.BAD_REQUEST

    @app.patch('/admin/users/<user>')
    @auth.login_required
    def admin_change_password(user):
        if not request.is_json:
            return {"error": "Request must be JSON"}, status.UNSUPPORTED_MEDIA_TYPE

        if not is_admin(auth.current_user()):
            return "Unauthorized. Admin access only.", status.FORBIDDEN

        if user is None:
            return "No user input found.", status.BAD_REQUEST

        data = request.get_json()
        conn = create_connection(app.config[CONFIG_DB_PATH])

        try:
            if not is_user_existing(conn, user):
                return "User does not exist.", status.NOT_FOUND

            change_password(conn, user, data["password"])
            return {"username": user, "password": "***"}, status.CREATED
        except (KeyError, ValueError):
            return "Invalid Request", status.BAD_REQUEST

    @app.delete('/admin/users/<user>')
    @auth.login_required
    def admin_delete_user(user):
        if not is_admin(auth.current_user()):
            return "Unauthorized. Admin access only.", status.FORBIDDEN

        if user is None:
            return "No user input found. Please use '?user='", status.BAD_REQUEST

        conn = create_connection(app.config[CONFIG_DB_PATH])

        if not is_user_existing(conn, user):
            return "User not found.", status.NOT_FOUND

        delete_user(conn, user)
        return {}, status.OK

    @app.get('/pi/get/<data>')
    def pi_get(data):
        try:
            if data.isnumeric():
                return Pi.get_digit_at_index(i_pi, int(data)), status.OK
            if data == "getfile":
                return Pi.get_all_from_file(app.config[CONFIG_PI_TXT_PATH]), status.OK
            if "upto" in data and data.split("upto")[1].isnumeric():
                return Pi.get_digits_up_to(i_pi, int(data.split("upto")[1])), status.OK
            if data is not None:
                return Pi.get_next_ten_digits_for_user(i_pi, data, app.config[CONFIG_DB_PATH]), status.OK
        except ValueError:
            return {"error": "invalid value"}, status.BAD_REQUEST
        return {"error": "No known request sent"}, status.BAD_REQUEST

    @app.get('/e/get/<data>')
    def e_get(data):
        try:
            if data.isnumeric():
                return E.get_digit_at_index(i_e, int(data)), status.OK
            if data == "getfile":
                return E.get_all_from_file(app.config[CONFIG_E_TXT_PATH]), status.OK
            if "upto" in data and data.split("upto")[1].isnumeric():
                return E.get_digits_up_to(i_e, int(data.split("upto")[1])), status.OK
            if data is not None:
                return E.get_next_ten_digits_for_user(i_e, data, app.config[CONFIG_DB_PATH]), status.OK
        except ValueError:
            return {"error": "invalid value"}, status.BAD_REQUEST
        return {"error": "No known request sent"}, status.BAD_REQUEST

    @app.get('/sqrt2/get/<data>')
    def sqrt2_get(data):
        try:
            if data.isnumeric():
                return Sqrt2.get_digit_at_index(i_sqrt2, int(data)), status.OK
            if data == "getfile":
                return Sqrt2.get_all_from_file(app.config[CONFIG_SQRT2_TXT_PATH]), status.OK
            if "upto" in data and data.split("upto")[1].isnumeric():
                return Sqrt2.get_digits_up_to(i_sqrt2, int(data.split("upto")[1])), status.OK
            if data is not None:
                return Sqrt2.get_next_ten_digits_for_user(i_sqrt2, data, app.config[CONFIG_DB_PATH]), status.OK
        except ValueError:
            return {"error": "invalid value"}, status.BAD_REQUEST
        return {"error": "No known request sent"}, status.BAD_REQUEST

    @app.get('/pi')
    def pi():
        return Pi.get_next_ten_digits(i_pi, app.config[CONFIG_PI_TXT_PATH]), status.OK

    @app.get('/pi/<data>')
    def pi_user(data):
        if data.isnumeric():
            return Pi.get_digit_at_index(i_pi, int(data)), status.OK

        return Pi.get_next_ten_digits_for_user(i_pi, data, app.config[CONFIG_DB_PATH]), status.OK

    @app.delete('/pi/<user>')
    def pi_delete(user):
        reset_current_index(create_connection(app.config[CONFIG_DB_PATH]), user, "pi")
        return {}, status.OK

    @app.route("/pi/reset")
    def pi_reset():
        with open(app.config[CONFIG_PI_TXT_PATH], "w") as f:
            f.truncate()
        return "reset", status.OK

    @app.get('/e')
    def e():
        return E.get_next_ten_digits(i_e, app.config[CONFIG_E_TXT_PATH]), status.OK

    @app.get('/e/<data>')
    def e_user(data):
        if data.isnumeric():
            return E.get_digit_at_index(i_e, int(data)), status.OK

        return E.get_next_ten_digits_for_user(i_e, data, app.config[CONFIG_DB_PATH]), status.OK

    @app.delete('/e/<user>')
    def e_delete(user):
        reset_current_index(create_connection(app.config[CONFIG_DB_PATH]), user, "e")
        return {}, status.OK

    @app.route("/e/reset")
    def e_reset():
        with open(app.config[CONFIG_E_TXT_PATH], "w") as f:
            f.truncate()
        return "reset"

    @app.get('/sqrt2')
    def sqrt2():
        return Sqrt2.get_next_ten_digits(i_sqrt2, app.config[CONFIG_SQRT2_TXT_PATH]), status.OK

    @app.get('/sqrt2/<data>')
    def sqrt2_user(data):
        if data.isnumeric():
            return Sqrt2.get_digit_at_index(i_sqrt2, int(data)), status.OK

        return Sqrt2.get_next_ten_digits_for_user(i_sqrt2, data, app.config[CONFIG_DB_PATH]), status.OK

    @app.delete('/sqrt2/<user>')
    def sqrt2_delete(user):
        reset_current_index(create_connection(app.config[CONFIG_DB_PATH]), user, "sqrt2")
        return {}, status.OK

    @app.route("/sqrt2/reset")
    def sqrt2_reset():
        with open(app.config[CONFIG_SQRT2_TXT_PATH], "w") as f:
            f.truncate()
        return "reset"

    return app


if __name__ == "__main__":
    create_app().run()
