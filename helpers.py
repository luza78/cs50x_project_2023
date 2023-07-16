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
    sql = "UPDATE users SET name = ?, hash = ? WHERE email = ?;"
    update = (name, hash, email)
    cur.execute(sql, update)

    conn.commit()

    # Close connection
    conn.close()
    return

def admin_get_users():
    # Connect Database
    conn = sqlite3.connect("intranet.db")
    
    # Enable it to return as dict
    conn.row_factory = sqlite3.Row

    # Create cursor
    cur = conn.cursor()

    # Lookup in db
    cur.execute("SELECT name, email, type FROM users ORDER BY type, name;")

    # Make our return element a list
    db_lookup = []

    # Add dicts to list
    for num in cur.fetchall():
        num = dict(num)
        db_lookup.append(num)

    # Close connection
    conn.close()
    return db_lookup

def admin_remove_user(email):
    conn = sqlite3.connect("intranet.db")
    
    # Create cursor
    cur = conn.cursor()

    # Deletes user from DB
    sql = "DELETE FROM users WHERE email = ?;"
    remove = (email, )
    cur.execute(sql, remove)

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
    name = "~ User not registered ~"
    sql = "INSERT INTO users(name, email, type) VALUES(?, ?, ?);"
    insert = (name, email, type)
    cur.execute(sql, insert)

    conn.commit()

    # Close connection
    conn.close()
    return

def admin_reset_user_password(email):
    # Connect Database
    conn = sqlite3.connect("intranet.db")
    # Create cursor
    cur = conn.cursor()
    hash = ""

    # Resets User hash in DB allowing them to register again
    sql = "UPDATE users SET hash = ? WHERE email = ?;"
    update = (hash, email)
    cur.execute(sql, update)

    conn.commit()

    # Close connection
    conn.close()
    return

def admin_change_user_type(email, type):
    # Connect Database
    conn = sqlite3.connect("intranet.db")
    # Create cursor
    cur = conn.cursor()

    # Update db, chaning the user type
    sql = "UPDATE users SET type = ? WHERE email = ?;"
    update = (type, email)
    cur.execute(sql, update)

    conn.commit()

    # Close connection
    conn.close()
    return

def upload_schedule(filename):
    # Connect Database
    conn = sqlite3.connect("intranet.db")
    
    # Create cursor
    cur = conn.cursor()

    # Update db, registering the user
    
    sql = "INSERT INTO schedule(name) VALUES(?);"
    insert = (filename, )
    cur.execute(sql, insert)

    conn.commit()

    # Close connection
    conn.close()
    return

def upload_schedule_is_week(filename):
    # Connect Database
    conn = sqlite3.connect("intranet.db")
    
    # Create cursor
    cur = conn.cursor()

    # Update db, registering the user
    
    sql = "INSERT INTO schedule(name, type) VALUES(?, 'week');"
    insert = (filename, )
    cur.execute(sql, insert)

    conn.commit()

    # Close connection
    conn.close()
    return

def upload_casting(data, filename):
    # Connect Database
    conn = sqlite3.connect("intranet.db")
    
    # Create cursor
    cur = conn.cursor()

    # Update db, registering the user
    
    sql = "INSERT INTO casting(name, file) VALUES(?, ?);"
    insert = (filename, data)
    cur.execute(sql, insert)

    conn.commit()

    # Close connection
    conn.close()
    return

def remove_casting(id):
    conn = sqlite3.connect("intranet.db")
    
    # Create cursor
    cur = conn.cursor()

    # Deletes user from DB
    sql = "DELETE FROM casting WHERE id = ?;"
    remove = (id, )
    cur.execute(sql, remove)

    conn.commit()

    # Close connection
    conn.close()
    return

def get_casting():
    # Connect Database
    conn = sqlite3.connect("intranet.db")
    
    # Enable it to return as dict
    conn.row_factory = sqlite3.Row

    # Create cursor
    cur = conn.cursor()

    # Lookup in db
    cur.execute("SELECT id, name, uploaded from casting;")

    # Make our return element a list
    db_lookup = []

    # Add dicts to list
    for num in cur.fetchall():
        num = dict(num)
        db_lookup.append(num)

    # Close connection
    conn.close()
    return db_lookup

def get_casting_file(id):
    # Connect Database
    conn = sqlite3.connect("intranet.db")
    
    # Create cursor
    cur = conn.cursor()

    # Update db, registering the user
    
    sql = "SELECT file, name FROM casting WHERE id = ?;"
    #insert = (filename, data)
    cur.execute(sql, id)

    db_lookup = cur.fetchone()

    # Close connection
    conn.close()
    return db_lookup

def schedule_today():
    # Connect Database
    conn = sqlite3.connect("intranet.db")
    # Create cursor
    cur = conn.cursor()

        # Lookup in db
    cur.execute("SELECT name FROM schedule WHERE type = 'day' ORDER BY uploaded DESC LIMIT 1;")

    db_lookup = cur.fetchone()

    # Close connection
    conn.close()
    return db_lookup

def schedule_week():
    # Connect Database
    conn = sqlite3.connect("intranet.db")
    # Create cursor
    cur = conn.cursor()

        # Lookup in db
    cur.execute("SELECT name FROM schedule WHEREle WHERE type = 'week' ORDER BY uploaded DESC LIMIT 1;")

    db_lookup = cur.fetchone()

    # Close connection
    conn.close()
    return db_lookup



def login_required(f):
    # Makes sure user is logged in, else redirects to login page
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def login_required_admin(f):
    # Makes sure user is logged in, else redirects to login page
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None or session.get("user_type") != "admin":
            return redirect("/logout")
        return f(*args, **kwargs)
    return decorated_function