from flask import Flask, render_template, redirect, request, session, flash, send_file
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
from helpers import login_required, get_user, register_user, admin_add_user

# Configure Flask
app = Flask(__name__)


# Use filesystem instead of cookies
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


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
        
        # Looks for email in user database
        db_lookup = get_user(email)
        
        # Handles if email not found
        if not db_lookup:
            flash("Email is not recognized")
            return render_template("login.html")
        
        # Need to hash password etc
        if not check_password_hash(db_lookup[1], password):
            flash("Incorrect password")
            return render_template("login.html")
        else:
            # Starts session (user_id is the email, user type is type)
            session['user_id'] = db_lookup[0]
            session['user_type'] = db_lookup[2]
            return redirect("/")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    
    if request.method == "POST":
        
        # Get form inputs
        email = request.form.get("email")
        name = request.form.get("name")
        password = request.form.get("password")

        # Validate inputs
        if not email:
            flash("Enter an email address")
            return render_template("register.html")
        
        if not name:
            flash("Enter your name")
            return render_template("register.html")
        
        if not password:
            flash("Enter a password")
            return render_template("register.html")
        
        elif len(password) < 4:
            flash("Password must be longer than 4 characters")
            return render_template("register.html")
        
        # Look email up in DB
        db_email = get_user(email)

        if not db_email:
            flash("Email not found")
            return render_template("register.html")
        
        # Sees if user already exists
        elif db_email[1]:
            flash("User already exists")
            return render_template("register.html")
        
        # Hash password
        hash = generate_password_hash(password)

        # Update name & hash where email matches
        register_user(name, hash, email)

        return redirect("/")
    return render_template("register.html")

@app.route("/logout")
def logout():
    
    # Clears current session data
    session.clear()

    # Redirects to login
    return redirect("/")


@app.route("/download/<string:dl_id>")
@login_required
def download(dl_id):
    
    if dl_id:
        
        path="/Users/starkindustries/Desktop/project/webapp/static/downloads/" + dl_id

        return send_file(path, dl_id, as_attachment=True)
    
    else:
        
        return redirect("/documents")


@app.route("/")
@login_required
def index():
    
    return render_template("index.html")

@app.route("/planner")
@login_required
def planner():
    
    return redirect("static/22_23_planner.pdf")

@app.route("/documents")
@login_required
def documents():
    
    return render_template("documents.html")

@app.route("/admin")
@login_required
def admin():
    
    return render_template("admin.html")

@app.route("/users")
@login_required
def users():
    
    return render_template("users.html")

@app.route("/editusers", methods=["POST"])
@login_required
def editusers():
    
    return redirect("/users")

@app.route("/adduser", methods=["POST"])
@login_required
def adduser():

    email = request.form.get("email")
    type = request.form.get("type")

    # Validate input
    if not email:
        flash("Enter an email address", "error")
        return redirect("/users")
    
    if not type:
        flash("Type select error", "error")
        return redirect("/users")
    
    # Check email address is available
    db_lookup = get_user(email)

    if db_lookup:
        flash("Email already in use", "error")
        return redirect("/users")
    
    else:
        admin_add_user(email, type)
        flash("User added", "green")
        return redirect("/users")



if __name__ == "__main__":
    app.run(debug=True)