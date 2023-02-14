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


def get_current_index(conn, user):
    c = conn.cursor()
    c.execute("SELECT current_index FROM user WHERE username=:username", {'username': user})
    index = c.fetchone()
    conn.commit()
    if index is None:
        return -1
    else:
        return index[0]


def raise_current_index(conn, user, increment):
    c = conn.cursor()
    updated_index = get_current_index(conn, user) + increment
    c.execute("UPDATE user SET current_index =:index WHERE username =:username",
              {'index': updated_index, 'username': user})
    conn.commit()


def reset_current_index(conn, user):
    c = conn.cursor()
    c.execute("UPDATE user SET current_index =:index WHERE username =:username", {'index': 0, 'username': user})
    conn.commit()


def get_password(conn, user):
    c = conn.cursor()
    c.execute("SELECT password FROM user WHERE username =:username", {'username': user})
    pw = c.fetchone()
    conn.commit()
    if pw is None:
        return None
    return pw[0]


def create_user(conn, user, password):
    c = conn.cursor()
    c.execute("INSERT INTO user VALUES  (:username, :current_index, :password)",
              {'username': user, 'current_index': 0, 'password': password})
    conn.commit()
    return c.lastrowid


def create_user_table():
    if not os.path.exists("./db"):  # Creates the database directory, if it does not exist yet
        os.mkdir("./db")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(""" CREATE TABLE IF NOT EXISTS user (
                username text PRIMARY KEY,
                current_index integer,
                password text
                ); """)
    conn.commit()

    create_test_users(c, conn)


def create_test_users(c, conn):
    # 2 predefined users: "joerg" and "felix"
    c.execute("SELECT COUNT(*) FROM user")
    if c.fetchone()[0] == 0:
        create_user(conn, "joerg", generate_password_hash("elsa"))
        create_user(conn, "felix", generate_password_hash("mady"))
    conn.commit()
