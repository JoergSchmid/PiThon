import http
from collections import namedtuple
from flask import Flask, request, send_file, render_template, redirect, session
from flask_httpauth import HTTPBasicAuth
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
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
CLASS_MAPPING = {Pi.name: Pi, E.name: E, Sqrt2.name: Sqrt2}
STD_DIGIT_AMOUNT = 10

Err = namedtuple("Err", ["is_err", "message", "status"], defaults=None)


def create_app(storage_folder="./db/"):
    """
    Formatted according to https://flask.palletsprojects.com/en/2.2.x/tutorial/factory/
    :param storage_folder: folder the database should use
    :return: app
    """
    app = Flask(__name__)
    app.config[CONFIG_DB_PATH] = Path(storage_folder) / "pithon.db"
    app.config[CONFIG_PI_TXT_PATH] = Path(storage_folder) / "pi.txt"
    app.config[CONFIG_E_TXT_PATH] = Path(storage_folder) / "e.txt"
    app.config[CONFIG_SQRT2_TXT_PATH] = Path(storage_folder) / "sqrt2.txt"
    txt_path_mapping = {Pi.name: app.config[CONFIG_PI_TXT_PATH], E.name: app.config[CONFIG_E_TXT_PATH],
                        Sqrt2.name: app.config[CONFIG_SQRT2_TXT_PATH]}
    app.config["SECRET_KEY"] = "PiThon"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
    app.config["SESSION_TYPE"] = "sqlalchemy"
    db = SQLAlchemy(app)
    app.config["SESSION_SQLALCHEMY"] = db
    auth = HTTPBasicAuth()
    Session(app)

    with app.app_context():
        db.create_all()

    create_db_tables(app.config[CONFIG_DB_PATH])
    conn = create_connection(app.config[CONFIG_DB_PATH])

    def check_user_exists(user) -> Err:
        if not db_is_user_existing(conn, user):
            return Err(True, "User does not exist.", status.NOT_FOUND)
        return Err(False, None, None)

    def check_username_legal(user) -> Err:
        if db_is_user_existing(conn, user):
            return Err(True, "User already exists.", status.CONFLICT)
        if len(user) < 2:
            return Err(True, "Name too short.", status.FORBIDDEN)
        if user in FORBIDDEN_NAMES:
            return Err(True, "Illegal name", status.FORBIDDEN)
        return Err(False, None, None)

    def check_user_is_admin(user) -> Err:
        if db_get_rank(conn, user) != "admin":
            return Err(True, "Admin access only.", status.FORBIDDEN)
        return Err(False, None, None)

    def check_password(user, password) -> Err:
        if not check_password_hash(db_get_password(conn, user), password):
            return Err(True, "Wrong username or password.", status.FORBIDDEN)
        return Err(False, None, None)

    def check_request_is_json(data) -> Err:
        if not data.is_json:
            return Err(True, "Request must be JSON.", status.UNSUPPORTED_MEDIA_TYPE)
        return Err(False, None, None)

    def check_is_known_number(number):
        if number not in CLASS_MAPPING.keys():
            return Err(True, "Unknown number.", status.NOT_FOUND)
        return Err(False, None, None)

    def create_text_with_link_response(text, http_status, link_message="Continue", path=""):
        return f"""<p>{text}</p><br>
                   <a href=/{path}>{link_message}</a>""", http_status

    def api_get_username():
        user = request.authorization.username if request.authorization is not None else None
        if user is None:
            user = session.get("username")
            if user is None:
                raise RuntimeError({"message": "No username given. Please log in or use auth.", "status": status.NOT_FOUND})
        elif not verify_password(user, request.authorization.password):
            raise RuntimeError({"message": "Wrong username or password.", "status": status.NOT_FOUND})
        return user

    def api_get_number():
        number = request.args.get("number")
        if number is not None:
            if number not in CLASS_MAPPING.keys():
                raise RuntimeError({"message": "Unknown number.", "status": status.NOT_FOUND})
            return number
        return None

    def api_get_index():
        index = request.args.get("index")
        if index is not None:
            if not index.isnumeric or int(index) < 0:
                raise RuntimeError({"message": "Invalid index.", "status": status.BAD_REQUEST})
            return int(index)
        return None

    def api_get_amount():
        amount = request.args.get("amount")
        if amount is not None:
            if not amount.isnumeric or int(amount) < 0:
                raise RuntimeError({"message": "Invalid amount.", "status": status.BAD_REQUEST})
            return int(amount)
        return None

    @app.get('/api/user')
    def api_get_number_with_user():
        try:
            user = api_get_username()
            number = api_get_number()
            index = api_get_index()
            amount = api_get_amount()
        except RuntimeError as err:
            return render_template("api_help.jinja", message=err.args.index("message")), err.args.index("status")

        if number is None or index is not None:
            return render_template("api_help.jinja", message="Unknown operation."), status.BAD_REQUEST

        number_instance = CLASS_MAPPING[number]()

        if amount is None:
            return number_instance.get_digits(0, db_get_current_index(conn, user, number)), status.OK
        return number_instance.get_digits_for_user(user, amount, app.config[CONFIG_DB_PATH]), status.OK

    @app.get('/api')
    def api_get_number_without_user():
        try:
            number = api_get_number()
            index = api_get_index()
            amount = api_get_amount()
        except RuntimeError as err:
            return render_template("api_help.jinja", message=err.args.index("message")), err.args.index("status")

        if number is None:
            return render_template("api_help.jinja"), status.BAD_REQUEST

        number_instance = CLASS_MAPPING[number]()
        path = txt_path_mapping[number]

        if index is None:
            if amount is None:
                return number_instance.get_all_from_file(path), status.OK
            return number_instance.get_next_digits_for_txt_file(amount, path), status.OK

        if amount is None:
            return number_instance.get_digit_at_index(index), status.OK
        return number_instance.get_digits(index, amount), status.OK

    @app.post('/api/user')
    def api_post_set_user_index():
        try:
            user = api_get_username()
            number = api_get_number()
            index = api_get_index()
        except RuntimeError as err:
            return render_template("api_help.jinja", message=err.args.index("message")), err.args.index("status")

        if number is None or index is None:
            return render_template("api_help.jinja", message="Unknown request."), status.BAD_REQUEST

        db_set_current_index(conn, user, number, index)
        return f"Index of {number} for {user} successfully set to {index}.", status.OK

    @app.post('/api')
    def api_post_create_new_user():
        req = request.get_json() if request.is_json else None

        if req is None or req["username"] is None or req["password"] is None:
            return render_template("api_help.jinja", message="Insufficient json data."), status.BAD_REQUEST

        if db_is_user_existing(conn, req["username"]):
            return render_template("api_help.jinja", message="User already exists."), status.CONFLICT

        db_create_user(conn, req["username"], req["password"])
        return f"{req['username']} successfully created.", status.CREATED

    @app.delete('/api/user')
    def api_delete_user():
        try:
            user = api_get_username()
        except RuntimeError as err:
            return render_template("api_help.jinja", message=err.args.index("message")), err.args.index("status")
        req = request.get_json() if request.is_json else None

        if req is None or not req["confirm_deletion"]:
            return render_template("api_help.jinja", message="Insufficient json data."), status.BAD_REQUEST
        db_delete_user(conn, user)
        return f"{user} successfully deleted.", status.OK

    @app.delete('/api')
    def api_reset_number():
        try:
            number = api_get_number()
        except RuntimeError as err:
            return render_template("api_help.jinja", message=err.args.index("message")), err.args.index("status")
        path = txt_path_mapping[number]
        if number is not None:
            with open(path, "w") as f:
                f.truncate()
            return f"{number} successfully reset.", status.OK
        return render_template("api_help.jinja", message="Number missing."), status.BAD_REQUEST

    @app.get('/api/download')
    def download_file():
        try:
            number = api_get_number()
        except RuntimeError as err:
            return render_template("api_help.jinja", message=err.args.index("message")), err.args.index("status")
        path = app.config[CONFIG_TXT_PATH_MAPPING[number]]
        if os.path.exists(path):
            return send_file(path, as_attachment=True), status.OK
        return "File not found", status.NOT_FOUND

    @app.route('/')
    def homepage():
        return render_template("homepage.jinja"), status.OK

    @auth.verify_password
    def verify_password(username, password):
        pw_hash = db_get_password(conn, username)
        return pw_hash is not None and check_password_hash(db_get_password(conn, username), password)

    @app.route('/tic_tac_toe')
    def tic_tac_toe():
        return render_template("tic_tac_toe.jinja")

    @app.route('/digits')
    def digits_ajax_view():
        return render_template("digits.jinja"), status.OK

    @app.route('/toggle_theme')
    def toggle_theme():
        if session.get("theme") == "dark":
            session["theme"] = "light"
        else:
            session["theme"] = "dark"
        return "", status.OK

    @app.route('/profile')
    def profile():
        return render_template("profile.jinja"), status.OK

    @app.post('/login')
    def login():
        username = request.form["username"]
        password = request.form["password"]
        if not verify_password(username, password):
            return "Wrong username or password.", status.FORBIDDEN
        session["username"] = username
        session["rank"] = db_get_rank(conn, username)
        last_page = request.args.get("current_page")
        if last_page is None:
            return "Logged in as " + session["username"], status.OK
        return redirect(last_page)

    @app.route('/logout')
    def logout():
        session.pop('username', None)
        last_page = request.args.get("current_page")
        if last_page is None:
            return "Logged out.", status.OK
        return redirect(request.args.get("current_page"))

    @app.post('/register')
    def register():
        username = request.form["username"]
        password = request.form["password"]

        if request.form["confirm_password"] != password:
            return "Password confirmation failed.", status.FORBIDDEN

        check = check_username_legal(username)
        if check.is_err:
            return check.message, check.status

        try:
            db_create_user(conn, username, password)
            session["username"] = username
            last_page = request.args.get("current_page")
            if last_page is None:
                return create_text_with_link_response("Welcome to PiThon, " + username + " :)", status.CREATED)
            return redirect(request.args.get("current_page"))
        except (KeyError, ValueError):
            return "Invalid Request", status.BAD_REQUEST

    @app.route('/delete', methods=['POST', 'DELETE'])
    def delete():
        username = session.get("username")
        password = request.form["password"]

        try:
            check = check_user_exists(username)
            if check.is_err:
                return check.message, check.status
            check = check_password(username, password)
            if check.is_err:
                return check.message, check.status

            db_delete_user(conn, username)
            session.pop('username', None)
            return create_text_with_link_response(f"{username} deleted :(", status.OK)
        except (KeyError, ValueError):
            return "Invalid Request", status.BAD_REQUEST

    @app.route('/db/<num>/<int:index>')
    def number_digits_view(num, index):
        check = check_is_known_number(num)
        if check.is_err:
            return create_text_with_link_response(check.message, check.message)
        return get_digit_from_number_digits(conn, CLASS_MAPPING[num], index), status.OK

    @app.route('/admin')
    def admin():
        username = session.get("username")
        check = check_user_is_admin(username)
        if check.is_err:
            return create_text_with_link_response(check.message, check.status)

        users_and_indices, numbers_and_indices = db_get_user_data_for_admin_panel(conn)
        users, ranks = zip(*users_and_indices)
        numbers, indices = zip(*numbers_and_indices)
        user_list = list(users)
        rank_list = list(ranks)
        number_list = list(numbers)
        index_list = list(indices)

        return render_template("admin_panel.jinja", user_list=user_list, rank_list=rank_list, number_list=number_list,
                               index_list=index_list), status.OK

    @app.route('/admin/delete', methods=['DELETE', 'POST'])
    def admin_delete():
        username = session.get("username")
        check = check_user_is_admin(username)
        if check.is_err:
            return create_text_with_link_response(check.message, check.status)

        user = request.args.get("user")
        if db_get_rank(conn, user) == "admin":
            return "You can´t delete admins.", status.FORBIDDEN

        db_delete_user(conn, user)
        return redirect("/admin")

    @app.get('/admin/users')
    @auth.login_required
    def admin_get_all_users():
        check = check_user_is_admin(auth.current_user())
        if check.is_err:
            return check.message, check.status

        users = db_get_all_user_names(conn)
        return users, status.OK

    @app.post('/admin/users')
    @auth.login_required
    def admin_add_user():
        check = check_user_is_admin(auth.current_user())
        if check.is_err:
            return check.message, check.status
        check = check_request_is_json(request)
        if check.is_err:
            return check.message, check.status
        data = request.get_json()
        check = check_username_legal(data["username"])
        if check.is_err:
            return check.message, check.status
        try:
            db_create_user(conn, data["username"], data["password"])
            return data["username"], status.CREATED
        except (KeyError, ValueError):
            return "Invalid Request", status.BAD_REQUEST

    @app.patch('/admin/users/<user>')
    @auth.login_required
    def admin_change_password(user):
        check = check_user_exists(user)
        if check.is_err:
            return check.message, check.status
        check = check_user_is_admin(auth.current_user())
        if check.is_err:
            return check.message, check.status
        check = check_request_is_json(request)
        if check.is_err:
            return check.message, check.status

        data = request.get_json()

        try:
            db_set_password(conn, user, data["password"])
            return {"username": user, "password": "***"}, status.CREATED
        except (KeyError, ValueError):
            return "Invalid Request", status.BAD_REQUEST

    @app.delete('/admin/reset_all_indices')
    @auth.login_required
    def admin_reset_all_indices():
        check = check_user_is_admin(auth.current_user())
        if check.is_err:
            return check.message, check.status

        db_reset_all_current_indices(conn)
        return "All indices are reset.", status.OK

    @app.delete('/admin/users/<user>')
    @auth.login_required
    def admin_delete_user(user):
        check = check_user_exists(user)
        if check.is_err:
            return check.message, check.status
        check = check_user_is_admin(auth.current_user())
        if check.is_err:
            return check.message, check.status

        db_delete_user(conn, user)
        return {}, status.OK

    @app.after_request
    def add_header(response):
        if request.method == "GET":
            response.headers['Cache-Control'] = 'no-store, max-age=0'
        return response

    return app


if __name__ == "__main__":
    create_app().run()
