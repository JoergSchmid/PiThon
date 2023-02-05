import sqlite3
from sqlite3 import Error


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


#    finally:
#        if conn:
#            conn.close()


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
    c.execute("UPDATE user SET current_index =:index WHERE username=:username",
              {'index': updated_index, 'username': user})
    conn.commit()


def create_user(conn, user):
    c = conn.cursor()
    c.execute("INSERT INTO user VALUES  (:username, :current_index)", {'username': user, 'current_index': 0})
    conn.commit()
    return c.lastrowid


def create_user_table():
    database = r"C:\gitroot\PiThon\db\pi.db"

    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute(""" CREATE TABLE IF NOT EXISTS user (
                username text PRIMARY KEY,
                current_index integer
                ); """)
    conn.commit()

    create_test_users(c, conn)


def create_test_users(c, conn):
    # 2 predefined users: "joerg" and "felix"
    c.execute("SELECT * FROM user WHERE username=:username", {'username': 'joerg'})
    if c.fetchone() is None:
        create_user(conn, "joerg")
    c.execute("SELECT current_index FROM user WHERE username=:username", {'username': 'felix'})
    if c.fetchone() is None:
        create_user(conn, "felix")
    conn.commit()
