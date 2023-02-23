import http
from flask import Flask, request, send_file
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash
from database import *
from irrational_digits import Pi, E, Sqrt2, IrrationalDigits
from pathlib import Path

status = http.HTTPStatus
CONFIG_DB_PATH = "DB_PATH"
CONFIG_PI_TXT_PATH = "PI_TXT_PATH"
CONFIG_E_TXT_PATH = "E_TXT_PATH"
CONFIG_SQRT2_TXT_PATH = "SQRT2_TXT_PATH"


def create_standard_get_view(number_class, txt_path):
    number_instance = number_class()

    def get_view():
        return number_instance.get_next_ten_digits(txt_path), status.OK

    return get_view


def create_index_or_user_view(number_class, db_path):
    number_instance = number_class()

    def index_or_user_view(data):
        if data.isnumeric():
            return number_instance.get_digit_at_index(int(data)), status.OK

        return number_instance.get_next_ten_digits_for_user(data, db_path), status.OK

    return index_or_user_view


def create_delete_user_index_view(number_class, db_path):

    def delete_user_index_view(user):
        reset_current_index(create_connection(db_path), user, number_class.name)
        return {}, status.OK
    return delete_user_index_view


def create_number_reset_view(txt_path):

    def number_reset_view():
        with open(txt_path, "w") as f:
            f.truncate()
        return "reset", status.OK

    return number_reset_view


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

    number_configs = [(Pi, app.config[CONFIG_PI_TXT_PATH]),
                      (E, app.config[CONFIG_E_TXT_PATH]),
                      (Sqrt2, app.config[CONFIG_SQRT2_TXT_PATH])]
    for number, txt_path in number_configs:
        app.add_url_rule(f"/{number.name}", view_func=create_standard_get_view(number, txt_path),
                         endpoint=f"{number.name}_standard_get")
        app.add_url_rule(f"/{number.name}/<data>",
                         view_func=create_index_or_user_view(number, app.config[CONFIG_DB_PATH]),
                         endpoint=f"{number.name}_index_or_user")
        app.add_url_rule(f"/{number.name}/<user>",
                         view_func=create_delete_user_index_view(number, app.config[CONFIG_DB_PATH]),
                         methods=["DELETE"], endpoint=f"{number.name}_delete_user_index")
        app.add_url_rule(f"/{number.name}/reset", view_func=create_number_reset_view(txt_path),
                         endpoint=f"{number.name}_reset")

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

    return app


if __name__ == "__main__":
    create_app().run()
