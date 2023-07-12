from functools import wraps
from flask import session, redirect, render_template
import sqlite3

def get_user(email):
    # Connect Database
    conn = sqlite3.connect("intranet.db")
    # Create cursor
    cur = conn.cursor()

        # Lookup in db
    cur.execute("SELECT email, hash, type FROM users WHERE email = ?;", [email])

    db_lookup = cur.fetchone()

    # Close connection
    conn.close()
    return db_lookup

def register_user(name, hash, email):
    # Connect Database
    conn = sqlite3.connect("intranet.db")
    # Create cursor
    cur = conn.cursor()

    # Update db, registering the user
    sql = "UPDATE users SET name = ?, hash = ?, type = 'standard' WHERE email = ?;"
    update = (name, hash, email)
    cur.execute(sql, update)

    conn.commit()

    # Close connection
    conn.close()
    return

def admin_add_user(email, type):
    # Connect Database
    conn = sqlite3.connect("intranet.db")
    # Create cursor
    cur = conn.cursor()

    # Update db, registering the user
    sql = "INSERT INTO users(email, type) VALUES(?, ?);"
    insert = (email, type)
    cur.execute(sql, insert)

    conn.commit()

    # Close connection
    conn.close()
    return


def login_required(f):
    # Makes sure user is logged in, else redirects to login page
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function