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


@app.route("/login")
def login():
    if request.method == "POST":
        return None
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