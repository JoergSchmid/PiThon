import os
import sqlite3
from sqlite3 import Error
from werkzeug.security import generate_password_hash

DB_PATH = "./db/pi.db"


def create_connection(db_file):
    """ create a database connection to the SQLite database
            specified by db_file
        :param db_file: database file
        :return: Connection object or None
        """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)


def db_execute(conn, query, parameters, fetchall=False):
    c = conn.cursor()
    try:
        c.execute(query, parameters)
    except Error:
        print("Error in db_execute()")
        return
    if fetchall:
        data = c.fetchall()
    else:
        data = c.fetchone()
    conn.commit()
    return data


def get_current_index(conn, user):
    index = db_execute(conn, "SELECT current_index FROM user WHERE username =:username", {'username': user})
    if index is None:
        return -1
    else:
        return index[0]


def raise_current_index(conn, user, increment):
    updated_index = get_current_index(conn, user) + increment
    db_execute(conn, "UPDATE user SET current_index =:index WHERE username =:username",
               {'index': updated_index, 'username': user})


def reset_current_index(conn, user):
    db_execute(conn, "UPDATE user SET current_index =:index WHERE username =:username", {'index': 0, 'username': user})


def get_password(conn, user):
    pw = db_execute(conn, "SELECT password FROM user WHERE username =:username", {'username': user})
    if pw is None:
        return None
    return pw[0]


def change_password(conn, user, password):
    db_execute(conn, "UPDATE user SET password =:password WHERE username =:username",
               {'password': password, 'username': user})


def get_user_data(conn, user):
    data = db_execute(conn, "SELECT * FROM user WHERE username =:username", {'username': user})
    return data


def get_all_user_names(conn):
    data = db_execute(conn, "SELECT username FROM user", {}, fetchall=True)  # fetchall()?
    return data


def create_user(conn, user, password):
    db_execute(conn, "INSERT INTO user VALUES  (:username, :current_index, :password)",
               {'username': user, 'current_index': 0, 'password': password})


def delete_user(conn, user):
    c = conn.cursor()
    c.execute("DELETE FROM user WHERE username =:username", {'username': user})
    conn.commit()


def is_user_existing(conn, user):
    c = conn.cursor()
    c.execute("SELECT username FROM user WHERE username =:username", {'username': user})
    data = c.fetchone()
    conn.commit()
    return data is not None


def create_user_table():
    if not os.path.exists("./db"):  # Creates the database directory, if it does not exist yet
        os.mkdir("./db")

    conn = sqlite3.connect(DB_PATH)
    db_execute(conn, """ CREATE TABLE IF NOT EXISTS user (
                    username text PRIMARY KEY,
                    current_index integer,
                    password text
                    ); """, {})
    create_test_users(conn)


def create_test_users(conn):
    # 2 predefined users: "joerg" and "felix". Created freshly for each session.
    # Permanent users are created on the admin endpoint.
    delete_user(conn, "joerg")
    delete_user(conn, "felix")
    create_user(conn, "joerg", generate_password_hash("elsa"))
    create_user(conn, "felix", generate_password_hash("mady"))
