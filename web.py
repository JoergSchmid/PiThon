import http
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

    number_configs = [(Pi, app.config[CONFIG_PI_TXT_PATH]),
                      (E, app.config[CONFIG_E_TXT_PATH]),
                      (Sqrt2, app.config[CONFIG_SQRT2_TXT_PATH])]

    def check_for_error(is_existing="", is_not_existing="", is_admin="", check_password="", check_request=None,
                        is_valid_number_name=""):
        username = is_existing if is_existing != "" else is_admin
        if check_password != "" and username == "":
            print("Internal error. Requested password check without providing a username to check_for_error().")
            return True, "Internal error.", status.INTERNAL_SERVER_ERROR

        if is_existing != "" and not db_is_user_existing(conn, is_existing):
            return True, "User does not exist.", status.NOT_FOUND
        if is_not_existing != "" and db_is_user_existing(conn, is_existing):
            return True, "User already exists.", status.CONFLICT
        if username != "" and username in FORBIDDEN_NAMES:
            return True, "Illegal name.", status.CONFLICT
        if is_admin != "" and db_get_rank(conn, is_admin) != "admin":
            return True, "Admin access only.", status.FORBIDDEN
        if check_password != "" and not check_password_hash(db_get_password(conn, username), check_password):
            return True, "Wrong username or password.", status.FORBIDDEN
        if username != "" and len(username) < 2:
            return True, "Name too short.", status.FORBIDDEN
        if check_request is not None and not check_request.is_json:
            return True, "Request must be JSON.", status.UNSUPPORTED_MEDIA_TYPE
        if is_valid_number_name != "" and is_valid_number_name not in CLASS_MAPPING.keys():
            return True, "Unknown number.", status.NOT_FOUND

        return False, None, None

    def create_text_with_link_response(text, http_status, link_message="Continue", page=""):
        return f"""<p>{text}</p><br>
                   <a href=/{page}>{link_message}</a>""", http_status

    @app.route('/api', methods=['GET', 'POST', 'DELETE'])
    def api():
        user = request.authorization.username if request.authorization is not None else None
        number_ = request.args.get("number")
        index_ = request.args.get("index")
        amount_ = request.args.get("amount")
        user_from_session = request.args.get("session")
        data = request.get_json() if request.is_json else None

        if user is not None and not verify_password(user, request.authorization.password):
            return render_template("api_help.jinja", message="Wrong username or password."), status.NOT_FOUND

        if user_from_session == "true":
            user = session.get("username")

        def get_class_and_path():
            for numberClass, txt_filepath in number_configs:
                if number_ == numberClass.name:
                    return numberClass(), txt_filepath
            return None, None

        if number_ is not None:
            if number_ not in ["pi", "e", "sqrt2"]:
                return render_template("api_help.jinja",
                                       message=f"{number_} is not a valid number."), status.NOT_FOUND

        if index_ is not None:
            if not index_.isnumeric() or int(index_) < 0:
                return render_template("api_help.jinja",
                                       message=f"{index_} is not a valid index."), status.BAD_REQUEST

        if amount_ is not None:
            if not amount_.isnumeric() or int(amount_) < 0:
                return render_template("api_help.jinja",
                                       message=f"{amount_} is not a valid amount."), status.BAD_REQUEST

        if request.method == "GET" and user is None and number_ is None and index_ is None and amount_ is None:
            return render_template("api_help.jinja"), status.OK

        num, path = get_class_and_path()
        index = int(index_) if index_ is not None else None
        amount = int(amount_) if amount_ is not None else None

        if request.method == "GET":
            # <--- No user given --->
            if user is None and number_ is not None and index is None and amount is None:
                return num.get_all_from_file(path), status.OK

            if user is None and number_ is not None and index is None:
                return num.get_next_digits_for_txt_file(amount, path), status.OK

            if user is None and number_ is not None and amount is None:
                return num.get_digit_at_index(index), status.OK

            if user is None and number_ is not None:
                return num.get_digits(index, amount), status.OK

            if user is None:
                return render_template("api_help.jinja", message="Help page :) (NYI)"), status.OK

            # <--- User given --->
            if number_ is not None and index is None and amount is None:
                return num.get_digits_for_user(user, 10, app.config[CONFIG_DB_PATH]), status.OK

            if number_ is not None and index is None:
                return num.get_digits_for_user(user, amount, app.config[CONFIG_DB_PATH]), status.OK

            if number_ is not None and amount is None:
                return render_template("api_help.jinja",
                                       message="No known operation available."), status.BAD_REQUEST

            if number_ is not None:
                return render_template("api_help.jinja",
                                       message="User, index & amount alone do not mix (yet)."), status.BAD_REQUEST

        if request.method == "POST":
            if user is None and number_ is None and index is None and amount is None:
                if data["username"] is None or data["password"] is None:
                    return render_template("api_help.jinja", message="Insufficient json data."), status.BAD_REQUEST

                if db_is_user_existing(conn, data["username"]):
                    return render_template("api_help.jinja", message="User already exists."), status.CONFLICT

                db_create_user(conn, data["username"], data["password"])
                return f"{data['username']} successfully created.", status.CREATED

            if user is not None and number_ is not None and index is not None and amount is None:
                db_set_current_index(conn, user, number_, index)
                return f"Index successfully set to {index}.", status.OK

        if request.method == "DELETE":
            if user is not None and number_ is None and index is None and amount is None:
                if data["confirm_deletion"]:
                    db_delete_user(conn, user)
                    return f"{user} successfully deleted.", status.OK
                return render_template("api_help.jinja", message="{'confirm_deletion'} needed."), status.BAD_REQUEST

            if user is not None and number_ is not None and index is None and amount is None:
                db_reset_current_index(conn, user, number_)
                return f"{number_} reset successful.", status.OK

            if user is None and number_ is not None and index is None and amount is None:
                with open(path, "w") as f:
                    f.truncate()
                return f"{number_} successfully reset.", status.OK

        return render_template("api_help.jinja", message="No valid input found."), status.BAD_REQUEST

    @app.route('/')
    def homepage():
        return render_template("homepage.jinja"), status.OK

    @auth.verify_password
    def verify_password(username, password):
        pw_hash = db_get_password(create_connection(app.config[CONFIG_DB_PATH]), username)
        return pw_hash is not None and check_password_hash(pw_hash, password)

    @app.route('/tic_tac_toe')
    def tic_tac_toe():
        return render_template("tic_tac_toe.jinja")

    @app.route('/digits')
    def digits_ajax_view():
        return render_template("digits.jinja"), status.OK

    @app.get('/digits/<number_name>')
    def download_file(number_name):
        check = check_for_error(is_valid_number_name=number_name)
        if check[0]:
            return create_text_with_link_response(f"{check[1]}", check[2])
        path = app.config[CONFIG_TXT_PATH_MAPPING[number_name]]
        if os.path.exists(path):
            return send_file(path, as_attachment=True), status.OK
        return "File not found", status.NOT_FOUND

    @app.route('/toggle_theme')
    def toggle_theme():
        if session.get("theme") == "dark":
            session["theme"] = "light"
        else:
            session["theme"] = "dark"
        return redirect(request.args.get("current_page"))

    @app.route('/profile')
    def profile():
        return render_template("profile.jinja"), status.OK

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == "POST":
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

        return """<form action='' method='POST'>
                  <input type='text' name='username'><br>
                  <input type='password' name='password'><br>
                  <input type='submit' value='Login'>
                  </form>""", status.OK

    @app.route('/logout')
    def logout():
        session.pop('username', None)
        last_page = request.args.get("current_page")
        if last_page is None:
            return "Logged out.", status.OK
        return redirect(request.args.get("current_page"))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]

            if request.form["confirm_password"] != password:
                return "Password confirmation failed.", status.FORBIDDEN

            check = check_for_error(is_not_existing=username)
            if check[0]:
                return check[1], check[2]

            try:
                db_create_user(conn, username, password)
                session["username"] = username
                last_page = request.args.get("current_page")
                if last_page is None:
                    return create_text_with_link_response("Welcome to PiThon, " + username + " :)", status.CREATED)
                return redirect(request.args.get("current_page"))
            except (KeyError, ValueError):
                return "Invalid Request", status.BAD_REQUEST
        return """<form action='' method='POST'>
                    <input type='text' name='username'><br>
                    <input type='password' name='password'><br>
                    <input type='password' name='confirm_password'><br>
                    <input type='submit' value='Register'>
                    </form>""", status.OK

    @app.route('/delete', methods=['GET', 'POST'])
    def delete():
        if request.method == "POST":
            username = session.get("username")
            password = request.form["password"]

            try:
                check = check_for_error(is_existing=username, check_password=password)
                if check[0]:
                    return check[1], check[2]

                db_delete_user(conn, username)
                session.pop('username', None)
                return create_text_with_link_response(f"{username} deleted :(", status.OK)
            except (KeyError, ValueError):
                return "Invalid Request", status.BAD_REQUEST
        return f"""<form action='' method='POST'>
                    <p>Confirm password to delete {session.get('username')}.</p><br>
                    <input type='password' name='password'><br>
                    <input type='submit' value='Delete'>
                    </form>""", status.OK

    @app.route('/db/<num>/<int:index>')
    def number_digits_view(num, index):
        check = check_for_error(is_valid_number_name=num)
        if check[0]:
            return create_text_with_link_response(f"{check[1]}", check[2])
        return get_digit_from_number_digits(conn, CLASS_MAPPING[num], index), status.OK

    @app.route('/admin')
    def admin():
        username = session.get("username")
        check = check_for_error(is_admin=username)
        if check[0]:
            return create_text_with_link_response(f"{check[1]}", check[2])

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
        check = check_for_error(is_admin=username)
        if check[0]:
            return create_text_with_link_response(f"{check[1]}", check[2])

        user = request.args.get("user")
        if db_get_rank(conn, user) == "admin":
            return "You can´t delete admins.", status.FORBIDDEN

        db_delete_user(conn, user)
        return redirect("/admin")

    @app.get('/admin/users')
    @auth.login_required
    def admin_get_all_users():
        check = check_for_error(is_admin=auth.current_user())
        if check[0]:
            return check[1], check[2]

        users = db_get_all_user_names(conn)
        return users, status.OK

    @app.post('/admin/users')
    @auth.login_required
    def admin_add_user():
        check = check_for_error(is_admin=auth.current_user(), check_request=request)
        if check[0]:
            return check[1], check[2]

        data = request.get_json()

        try:
            check = check_for_error(is_not_existing=data["username"])
            if check[0]:
                return check[1], check[2]

            db_create_user(conn, data["username"], data["password"])
            return data["username"], status.CREATED
        except (KeyError, ValueError):
            return "Invalid Request", status.BAD_REQUEST

    @app.patch('/admin/users/<user>')
    @auth.login_required
    def admin_change_password(user):
        check = check_for_error(is_existing=user, is_admin=auth.current_user(), check_request=request)
        if check[0]:
            return check[1], check[2]

        data = request.get_json()

        try:
            db_set_password(conn, user, data["password"])
            return {"username": user, "password": "***"}, status.CREATED
        except (KeyError, ValueError):
            return "Invalid Request", status.BAD_REQUEST

    @app.delete('/admin/reset_all_indices')
    @auth.login_required
    def admin_reset_all_indices():
        check = check_for_error(is_admin=auth.current_user())
        if check[0]:
            return check[1], check[2]

        db_reset_all_current_indices(conn)
        return "All indices are reset.", status.OK

    @app.delete('/admin/users/<user>')
    @auth.login_required
    def admin_delete_user(user):
        check = check_for_error(is_existing=user, is_admin=auth.current_user())
        if check[0]:
            return check[1], check[2]

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
