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
        conn = sqlite3.connect(db_file, check_same_thread=False)
        db_execute(conn, "PRAGMA foreign_keys = ON;", {})
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


# <--- Get Functions for tables "users" and "number_indices" --->
def db_get_all_user_data(conn, user):
    data = db_execute(conn, "SELECT * FROM users INNER JOIN users USING (user_id) WHERE username =:username",
                      {'username': user})
    return data


def db_get_all_user_names(conn):
    data = db_execute(conn, "SELECT username FROM users", {}, fetchall=True)
    usernames = [i[0] for i in data]  # Returns a normal tuple instead of the list of tuples in data
    return usernames


def db_get_password(conn, user):
    pw = db_execute(conn, "SELECT password FROM users WHERE username =:username", {'username': user})
    if pw is None:
        return None
    return pw[0]


def db_get_current_index(conn, user, num):
    index = db_execute(conn, "SELECT current_index FROM number_indices "
                             "INNER JOIN users ON users.user_id = number_indices.user_id "
                             "WHERE username =:username AND number =:number",
                       {'username': user, 'number': num})
    if index is None:
        return -1
    else:
        return index[0]


def db_get_rank(conn, user):
    rank = db_execute(conn, "SELECT rank FROM users WHERE username =:username", {'username': user})
    return rank[0] if rank is not None else None


def db_get_user_data_for_admin_panel(conn):
    users_and_ranks = db_execute(conn, "SELECT username, rank FROM users", {}, fetchall=True)
    numbers_and_indices = db_execute(conn, """SELECT number, current_index FROM users INNER JOIN number_indices
                                              ON users.user_id = number_indices.user_id""", {}, fetchall=True)
    return users_and_ranks, numbers_and_indices


# <--- (Re)Set Functions for tables "users" and "number_indices" --->
def db_set_password(conn, user, password):
    db_execute(conn, "UPDATE users SET password =:password WHERE username =:username",
               {'password': generate_password_hash(password), 'username': user})


def db_set_current_index(conn, user, num, index):
    db_execute(conn, "UPDATE number_indices SET current_index =:index "
                     "WHERE user_id = (SELECT user_id FROM users WHERE username =:username)"
                     "AND number =:number",
               {'index': index, 'username': user, 'number': num})


def db_raise_current_index(conn, user, num, increment):
    updated_index = db_get_current_index(conn, user, num) + increment
    db_set_current_index(conn, user, num, updated_index)


def db_reset_current_index(conn, user, num):
    db_execute(conn, "UPDATE number_indices SET current_index =:index "
                     "WHERE user_id = (SELECT user_id FROM users WHERE username =:username)"
                     "AND number =:number",
               {'index': 0, 'username': user, 'number': num})


def db_reset_all_current_indices_of_user(conn, user):
    db_execute(conn, "UPDATE number_indices SET current_index =:index "
                     "WHERE user_id = (SELECT user_id FROM users WHERE username =:username)",
               {'username': user, 'index': 0})


def db_reset_all_current_indices(conn):
    db_execute(conn, "UPDATE number_indices SET current_index =:index", {'index': 0})


def db_set_rank(conn, user, rank):
    db_execute(conn, "UPDATE users SET rank =:rank WHERE username =:username",
               {'rank': rank, 'username': user})


# <--- Create and delete users --->
def db_create_user(conn, user, password, rank="std"):
    if db_is_user_existing(conn, user) or user in FORBIDDEN_NAMES:
        return None
    db_execute(conn, "INSERT INTO users (username, password, rank) VALUES (:username, :password, :rank)",
               {'username': user, 'password': generate_password_hash(password), 'rank': rank})
    user_id = db_execute(conn, "SELECT user_id FROM users WHERE username =:username", {'username': user})
    db_execute(conn, "INSERT INTO number_indices (user_id, number)"
                     "VALUES (:user_id, :pi), (:user_id, :e), (:user_id, :sqrt2)",
               {'user_id': user_id[0], 'pi': "pi", 'e': "e", 'sqrt2': "sqrt2"})


def db_delete_user(conn, user):
    user_id = db_execute(conn, "SELECT user_id FROM users WHERE username =:username", {'username': user})
    if user_id is None:
        return
    # user var is a tuple when called with a delete request
    if len(user[0]) == 1:
        db_execute(conn, "DELETE FROM users WHERE username =:username", {'username': user})
    else:
        db_execute(conn, "DELETE FROM users WHERE username =:username", {'username': user[0]})


def db_is_user_existing(conn, user):
    data = db_execute(conn, "SELECT username FROM users WHERE username =:username", {'username': user})
    return data is not None


# <--- Table "number_digits" for saving digits for endpoint "/db/<number>/<index> --->
def get_digit_from_number_digits(conn, number, digit_index):
    def get_data():
        return db_execute(conn, "SELECT digit FROM number_digits WHERE number =:number AND digit_index =:digit_index",
                          {'number': number.name, 'digit_index': digit_index})

    data = get_data()
    if data is None:
        create_number_digits_index_up_to(conn, number, digit_index)
        data = get_data()
    return str(data[0])


def create_number_digits_index_up_to(conn, number, digit_index):
    next_index = int(db_execute(conn, "SELECT COUNT(*) FROM number_digits WHERE number =:number",
                                {'number': number.name})[0])
    all_digits = number().get_number_with_accuracy(int(digit_index))
    all_digits = all_digits.replace('.', '')
    for i in range(next_index, int(digit_index) + 1):
        db_execute(conn, "INSERT INTO number_digits (number, digit_index, digit)"
                         "VALUES (:number, :digit_index, :digit)",
                   {'number': number.name, 'digit_index': i, 'digit': all_digits[i]})


# <--- Create all database tables and test users below.  --->
def create_db_tables(path):
    conn = create_connection(path)
    create_users_table(conn)
    create_number_indices_table(conn)
    create_number_digits_table(conn)
    create_sql_indices(conn)
    create_test_users(conn)


def create_users_table(conn):
    db_execute(conn, """ CREATE TABLE IF NOT EXISTS users (
                    user_id integer PRIMARY KEY AUTOINCREMENT,
                    username text NOT NULL,
                    password text NOT NULL,
                    rank text NOT NULL
                    ); """, {})


def create_number_indices_table(conn):
    db_execute(conn, """ CREATE TABLE IF NOT EXISTS number_indices (
                    number text NOT NULL,
                    current_index integer DEFAULT 0,
                    user_id integer NOT NULL,
                    FOREIGN KEY (user_id)
                        REFERENCES users (user_id)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                    ); """, {})


def create_number_digits_table(conn):
    db_execute(conn, """ CREATE TABLE IF NOT EXISTS number_digits (
                    number text,
                    digit_index integer,
                    digit integer
                    ); """, {})


def create_sql_indices(conn):
    db_execute(conn, "CREATE INDEX IF NOT EXISTS number_digits_idx ON number_digits (number, digit_index)", {})


def create_test_users(conn):
    # 2 predefined users: "joerg" and "felix". Created freshly for each session.
    # Permanent users are created on the admin endpoint.
    db_delete_user(conn, TEST_USER_ADMIN[0])
    db_delete_user(conn, TEST_USER_STD[0])
    db_create_user(conn, TEST_USER_ADMIN[0], TEST_USER_ADMIN[1], rank="admin")
    db_create_user(conn, TEST_USER_STD[0], TEST_USER_STD[1])
