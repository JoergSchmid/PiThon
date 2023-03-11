import http
from flask import Flask, request, send_file, render_template, redirect
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

CONFIG_TXT_PATH_MAPPING = {Pi.name: CONFIG_PI_TXT_PATH, E.name: CONFIG_E_TXT_PATH, Sqrt2.name: CONFIG_SQRT2_TXT_PATH}


def create_standard_get_view(number_class, txt_path):
    number_instance = number_class()

    def get_view():
        return number_instance.get_next_ten_digits(txt_path), status.OK

    return get_view


def create_get_database_view(number_class, db_path):
    def get_view(digit_index):
        return get_digit_from_digit_index(create_connection(db_path), number_class, digit_index), status.OK

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


def create_delete_all_user_indices_view(db_path):
    def delete_all_user_indices_view(user):
        reset_all_current_indices_of_user(create_connection(db_path), user)
        return {}, status.OK

    return delete_all_user_indices_view


def create_number_reset_view(txt_path):
    def number_reset_view():
        with open(txt_path, "w") as f:
            f.truncate()
        return "reset", status.OK

    return number_reset_view


def create_get_view(number_class, txt_path, db_path):
    number_instance = number_class()

    def get_view(data):
        try:
            if data.isnumeric():
                return number_class.get_digit_at_index(number_instance, int(data)), status.OK
            if data == "getfile":
                return number_class.get_all_from_file(txt_path), status.OK
            if "upto" in data and data.split("upto")[1].isnumeric():
                return number_class.get_digits_up_to(number_instance, int(data.split("upto")[1])), status.OK
            if data is not None:
                return number_class.get_next_ten_digits_for_user(number_instance, data, db_path), status.OK
        except ValueError:
            return {"error": "invalid value"}, status.BAD_REQUEST
        return {"error": "No known request sent"}, status.BAD_REQUEST

    return get_view


def create_get_first_ten_view(number_class):
    def get_first_ten_view():
        return number_class().get_first_ten_digits_without_point(), status.OK

    return get_first_ten_view


def create_get_all_view(number_class, txt_path):
    def get_all_view():
        return number_class().get_all_from_file(txt_path), status.OK

    return get_all_view


def create_app(storage_folder="./db/"):
    """
    Formatted according to https://flask.palletsprojects.com/en/2.2.x/tutorial/factory/
    :param storage_folder: folder the database should use
    :return: app
    """
    app = Flask(__name__, static_folder="frontend", template_folder="frontend")
    app.config[CONFIG_DB_PATH] = Path(storage_folder) / "pithon.db"
    app.config[CONFIG_PI_TXT_PATH] = Path(storage_folder) / "pi.txt"
    app.config[CONFIG_E_TXT_PATH] = Path(storage_folder) / "e.txt"
    app.config[CONFIG_SQRT2_TXT_PATH] = Path(storage_folder) / "sqrt2.txt"

    auth = HTTPBasicAuth()

    create_db_tables(app.config[CONFIG_DB_PATH])

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
        app.add_url_rule(f"/reset/<user>",
                         view_func=create_delete_all_user_indices_view(app.config[CONFIG_DB_PATH]),
                         methods=["DELETE"], endpoint=f"{number.name}_delete_all_user_indices")
        app.add_url_rule(f"/{number.name}/reset", view_func=create_number_reset_view(txt_path),
                         endpoint=f"{number.name}_reset")
        app.add_url_rule(f"/{number.name}/get/<data>",
                         view_func=create_get_view(number, txt_path, app.config[CONFIG_DB_PATH]),
                         endpoint=f"{number.name}_get")
        app.add_url_rule(f"/db/{number.name}/<digit_index>",
                         view_func=create_get_database_view(number, app.config[CONFIG_DB_PATH]),
                         endpoint=f"{number.name}_get_database")
        app.add_url_rule(f"/{number.name}/get_first_ten", view_func=create_get_first_ten_view(number),
                         endpoint=f"/{number.name}_get_first_ten")
        app.add_url_rule(f"/get_all/{number.name}", view_func=create_get_all_view(number, txt_path),
                         endpoint=f"/{number.name}_get_all")

    @app.route('/')
    def homepage():
        return render_template("homepage.html"), status.OK

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

    @app.route('/tic-tac-toe')
    def tic_tac_toe():
        return render_template("tic_tac_toe.html")

    @app.route('/digits')
    def digits_view():
        return render_template("digits_form.html"), status.OK

    @app.route('/digits/form')
    def digits_form():  # HTML form @ '/digits'
        number_selection = request.args.get("number_selection")
        reset = request.args.get("reset")
        choose_mode = request.args.get("choose_mode")
        index = request.args.get("index")
        if reset is not None and reset == "Reset":
            return redirect(request.host_url + number_selection + "/reset", code=302)
        if choose_mode == "next_ten":
            return redirect(request.host_url + number_selection, code=302)
        if index is None or not index.isnumeric() or int(index) < 0:
            return "Invalid request.", status.BAD_REQUEST
        if choose_mode == "one_digit":
            return redirect(request.host_url + number_selection + "/" + index, code=302)
        return "Invalid request.", status.BAD_REQUEST

    @app.get('/digits/<number_name>')
    def download_file(number_name):
        if number_name not in CONFIG_TXT_PATH_MAPPING.keys():
            return "Unknown number", status.BAD_REQUEST
        path = app.config[CONFIG_TXT_PATH_MAPPING[number_name]]
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

    @app.delete('/admin/reset_all_indices')
    @auth.login_required
    def admin_reset_all_indices():
        if not is_admin(auth.current_user()):
            return "Unauthorized. Admin access only.", status.FORBIDDEN

        reset_all_current_indices(create_connection(app.config[CONFIG_DB_PATH]))
        return "All indices are reset.", status.OK

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

    @app.after_request
    def add_header(response):
        if request.method == "GET":
            response.headers['Cache-Control'] = 'no-store, max-age=0'
        return response

    return app


if __name__ == "__main__":
    create_app().run()
