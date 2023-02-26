import os
import sqlite3
from sqlite3 import Error
from werkzeug.security import generate_password_hash

TEST_USER_ADMIN = ("joerg", "elsa")
TEST_USER_STD = ("felix", "mady")
FORBIDDEN_NAMES = ["getfile", "upto", "get"]  # These words are commands.


def create_connection(db_file):
    """ create a database connection to the SQLite database
            specified by db_file
        :param db_file: database file
        :return: Connection object or None
        """
    folder = db_file.parent
    if not os.path.exists(folder):  # Creates the database directory, if it does not exist yet
        os.mkdir(folder)

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
        print(query, parameters)
        print("Error in db_execute()")
        return
    if fetchall:
        data = c.fetchall()
    else:
        data = c.fetchone()
    conn.commit()
    return data


def get_current_index(conn, user, num):
    index = None
    index = db_execute(conn, f"SELECT {num}_current_index FROM number_index "
                             f"INNER JOIN user ON user.user_id = number_index.user_id WHERE username =:username",
                       {'username': user})
    if index is None:
        return -1
    else:
        return index[0]


def raise_current_index(conn, user, increment, num):
    updated_index = get_current_index(conn, user, num) + increment
    db_execute(conn, f"UPDATE number_index SET {num}_current_index =:index WHERE user_id ="
                     f"(SELECT user_id FROM user WHERE username =:username)",
               {'index': updated_index, 'username': user})


def reset_current_index(conn, user, num):
    db_execute(conn, f"UPDATE number_index SET {num}_current_index =:index WHERE user_id ="
                     f"(SELECT user_id FROM user WHERE username =:username)",
               {'index': 0, 'username': user})


def get_password(conn, user):
    pw = db_execute(conn, "SELECT password FROM user WHERE username =:username", {'username': user})
    if pw is None:
        return None
    return pw[0]


def change_password(conn, user, password):
    db_execute(conn, "UPDATE user SET password =:password WHERE username =:username",
               {'password': generate_password_hash(password), 'username': user})


def get_user_data(conn, user):
    data = db_execute(conn, "SELECT * FROM user INNER JOIN user USING (user_id) WHERE username =:username",
                      {'username': user})
    return data


def get_all_user_names(conn):
    data = db_execute(conn, "SELECT username FROM user", {}, fetchall=True)
    usernames = [i[0] for i in data]  # Returns a normal tuple instead of the list of tuples in data
    return usernames


def create_user(conn, user, password):
    if is_user_existing(conn, user) or user in FORBIDDEN_NAMES:
        return None
    db_execute(conn, "INSERT INTO user (username, password) "
                     "VALUES (:username, :password)",
               {'username': user, 'password': generate_password_hash(password)})
    user_id = db_execute(conn, "SELECT user_id FROM user WHERE username =:username", {'username': user})
    db_execute(conn, "INSERT INTO number_index (user_id) VALUES (:user_id)", {'user_id': user_id[0]})


def delete_user(conn, user):
    db_execute(conn, "DELETE FROM user WHERE username =:username", {'username': user})


def is_user_existing(conn, user):
    data = db_execute(conn, "SELECT username FROM user WHERE username =:username", {'username': user})
    return data is not None


def create_db_tables(path):
    conn = create_connection(path)
    create_user_table(conn)
    create_number_index_table(conn)
    create_number_digit_table(conn)
    create_test_users(conn)


def create_user_table(conn):
    db_execute(conn, """ CREATE TABLE IF NOT EXISTS user (
                    user_id integer PRIMARY KEY AUTOINCREMENT,
                    username text NOT NULL,
                    password text NOT NULL
                    ); """, {})


def create_number_index_table(conn):
    db_execute(conn, """ CREATE TABLE IF NOT EXISTS number_index (
                    pi_current_index integer DEFAULT 0,
                    e_current_index integer DEFAULT 0,
                    sqrt2_current_index integer DEFAULT 0,
                    user_id integer NOT NULL,
                    FOREIGN KEY (user_id)
                        REFERENCES user (user_id)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                    ); """, {})


def create_number_digit_table(conn):
    db_execute(conn, """ CREATE TABLE IF NOT EXISTS number_digit (
                    number text,
                    digit_index integer,
                    digit integer
                    ); """, {})


def create_test_users(conn):
    # 2 predefined users: "joerg" and "felix". Created freshly for each session.
    # Permanent users are created on the admin endpoint.
    delete_user(conn, TEST_USER_ADMIN[0])
    delete_user(conn, TEST_USER_STD[0])
    create_user(conn, TEST_USER_ADMIN[0], TEST_USER_ADMIN[1])
    create_user(conn, TEST_USER_STD[0], TEST_USER_STD[1])
