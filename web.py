import http
from flask import Flask, request, send_file, render_template, redirect, session
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
    app = Flask(__name__)
    app.config[CONFIG_DB_PATH] = Path(storage_folder) / "pithon.db"
    app.config[CONFIG_PI_TXT_PATH] = Path(storage_folder) / "pi.txt"
    app.config[CONFIG_E_TXT_PATH] = Path(storage_folder) / "e.txt"
    app.config[CONFIG_SQRT2_TXT_PATH] = Path(storage_folder) / "sqrt2.txt"

    app.secret_key = "PiThon"
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

    def check_for_error(is_existing="", is_not_existing="", is_admin="", check_password="", check_request=None):
        conn = create_connection(app.config[CONFIG_DB_PATH])

        username = is_existing if is_existing is not "" else is_admin
        if check_password is not "" and username is "":
            print("Internal error. Requested password check without providing a username to check_for_error().")
            return True, "Internal error.", status.INTERNAL_SERVER_ERROR

        if is_existing is not "" and not is_user_existing(conn, is_existing):
            return True, "User does not exist.", status.NOT_FOUND
        if is_not_existing is not "" and is_user_existing(conn, is_existing):
            return True, "User already exists.", status.CONFLICT
        if username is not "" and username in FORBIDDEN_NAMES:
            return True, "Illegal name.", status.CONFLICT
        if is_admin is not "" and get_rank(conn, is_admin) != "admin":
            return True, "Admin access only.", status.FORBIDDEN
        if check_password is not "" and not check_password_hash(get_password(conn, username), check_password):
            return True, "Wrong username or password.", status.FORBIDDEN
        if username is not "" and len(username) < 2:
            return True, "Name too short.", status.FORBIDDEN
        if check_request is not None and not check_request.is_json:
            return True, "Request must be JSON.", status.UNSUPPORTED_MEDIA_TYPE

        return False, None, None

    def fancy_message(text, http_status, link_message="Continue", page=""):
        return f"""<p>{text}</p><br>
                   <a href=/{page}>{link_message}</a>""", http_status

    @app.route('/')
    def homepage():
        return render_template("homepage.jinja"), status.OK

    @auth.verify_password
    def verify_password(username, password):
        pw_hash = get_password(create_connection(app.config[CONFIG_DB_PATH]), username)
        return pw_hash is not None and check_password_hash(pw_hash, password)

    @app.route('/tic_tac_toe')
    def tic_tac_toe():
        return render_template("tic_tac_toe.jinja")

    @app.route('/digits_form')
    def digits_view():
        return render_template("digits_form.jinja"), status.OK

    @app.route('/digits_ajax')
    def digits_ajax_view():
        return render_template("digits_ajax.jinja"), status.OK

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

    @app.route('/toggle_theme')
    def toggle_theme():
        if session.get("theme") == "dark":
            session["theme"] = "light"
        else:
            session["theme"] = "dark"
        return redirect(request.args.get("current_page")), status.FOUND

    @app.route('/profile')
    def profile():
        return render_template("profile.jinja"), status.OK

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            if verify_password(username, password):
                session["username"] = username
            else:
                return "Wrong username or password.", status.FORBIDDEN
            last_page = request.args.get("current_page")
            if last_page is None:
                return "Logged in as " + session["username"], status.OK
            return redirect(last_page), status.FOUND

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
        return redirect(request.args.get("current_page")), status.FOUND

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

            conn = create_connection(app.config[CONFIG_DB_PATH])

            try:
                create_user(conn, username, password)
                session["username"] = username
                last_page = request.args.get("current_page")
                if last_page is None:
                    return fancy_message("Welcome to PiThon, " + username + " :)", status.CREATED)
                return redirect(request.args.get("current_page")), status.CREATED
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
            conn = create_connection(app.config[CONFIG_DB_PATH])

            try:
                check = check_for_error(is_existing=username, check_password=password)
                if check[0]:
                    return check[1], check[2]

                delete_user(conn, username)
                session.pop('username', None)
                return fancy_message(f"{username} deleted :(", status.OK)
            except (KeyError, ValueError):
                return "Invalid Request", status.BAD_REQUEST
        return f"""<form action='' method='POST'>
                    <p>Confirm password to delete {session.get('username')}.</p><br>
                    <input type='password' name='password'><br>
                    <input type='submit' value='Delete'>
                    </form>""", status.OK

    @app.route('/admin')
    def admin():
        username = session.get("username")
        check = check_for_error(is_admin=username)
        if check[0]:
            return fancy_message(f"{check[1]}", check[2])

        users_and_indices, numbers_and_indices = get_all_users_data(create_connection(app.config[CONFIG_DB_PATH]))
        print(users_and_indices)
        print(numbers_and_indices)
        users, ranks = zip(*users_and_indices)
        numbers, indices = zip(*numbers_and_indices)
        user_list = list(users)
        rank_list = list(ranks)
        number_list = list(numbers)
        index_list = list(indices)
        print(number_list)
        print(index_list)

        return render_template("admin_panel.jinja", user_list=user_list, rank_list=rank_list, number_list=number_list,
                               index_list=index_list), status.OK

    @app.route('/admin/delete')
    def admin_delete():
        username = session.get("username")
        check = check_for_error(is_admin=username)
        if check[0]:
            return fancy_message(f"{check[1]}", check[2])

        user = request.args.get("user")
        conn = create_connection(app.config[CONFIG_DB_PATH])
        if get_rank(conn, user) == "admin":
            return "You can´t delete admins.", status.FORBIDDEN

        delete_user(conn, user)
        return redirect("/admin"), status.OK

    @app.get('/admin/users')
    @auth.login_required
    def admin_get_all_users():
        check = check_for_error(is_admin=auth.current_user())
        if check[0]:
            return check[1], check[2]

        conn = create_connection(app.config[CONFIG_DB_PATH])

        users = get_all_user_names(conn)
        return users, status.OK

    @app.post('/admin/users')
    @auth.login_required
    def admin_add_user():
        check = check_for_error(is_admin=auth.current_user(), check_request=request)
        if check[0]:
            return check[1], check[2]

        data = request.get_json()
        conn = create_connection(app.config[CONFIG_DB_PATH])

        try:
            check = check_for_error(is_not_existing=data["username"])
            if check[0]:
                return check[1], check[2]

            create_user(conn, data["username"], data["password"])
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
        conn = create_connection(app.config[CONFIG_DB_PATH])

        try:
            change_password(conn, user, data["password"])
            return {"username": user, "password": "***"}, status.CREATED
        except (KeyError, ValueError):
            return "Invalid Request", status.BAD_REQUEST

    @app.delete('/admin/reset_all_indices')
    @auth.login_required
    def admin_reset_all_indices():
        check = check_for_error(is_admin=auth.current_user())
        if check[0]:
            return check[1], check[2]

        reset_all_current_indices(create_connection(app.config[CONFIG_DB_PATH]))
        return "All indices are reset.", status.OK

    @app.delete('/admin/users/<user>')
    @auth.login_required
    def admin_delete_user(user):
        check = check_for_error(is_existing=user, is_admin=auth.current_user())
        if check[0]:
            return check[1], check[2]

        delete_user(create_connection(app.config[CONFIG_DB_PATH]), user)
        return {}, status.OK

    @app.after_request
    def add_header(response):
        if request.method == "GET":
            response.headers['Cache-Control'] = 'no-store, max-age=0'
        return response

    return app


if __name__ == "__main__":
    create_app().run()
