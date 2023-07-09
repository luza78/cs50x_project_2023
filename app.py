from flask import Flask, render_template, redirect, request, session, flash
from flask_session import Session
import sqlite3
from helpers import login_required

# Configure Flask
app = Flask(__name__)


# Use filesystem instead of cookies
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Connect Database
conn = sqlite3.connect("/Users/starkindustries/Desktop/project/webapp/intranet.db")

# Create cursor
cur = conn.cursor()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        
        # Gets user input from form
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Checks for input
        if not email:
            flash("Enter an email address")
            return render_template("login.html")
        
        if not password:
            flash("Enter your password")
            return render_template("login.html")
        
        # Lookup in db
        db_lookup = cur.execute("SELECT email, hash FROM users WHERE email = ?;", email)
        
        # Looks to see if they match a user
        if not db_lookup["email"]:
            flash("Email is not recognized")
            return render_template("login.html")
        
        if not db_lookup["hash"]:
            flash("Incorrect password")
            return render_template("login.html")
        
        

        return redirect("/")
    return render_template("login.html")

@app.route("/register")
def register():
    if request.method == "POST":
        return None
    return render_template("register.html")


@app.route("/")
@login_required
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)