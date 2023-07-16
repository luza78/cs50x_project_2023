from helpers import (login_required, login_required_admin, get_user, register_user, admin_add_user,
                      admin_get_users, admin_remove_user, admin_change_user_type, admin_reset_user_password,
                        upload_casting, get_casting_file, get_casting, remove_casting, upload_schedule,
                          upload_schedule_is_week, schedule_today, schedule_week)

from flask import Flask, render_template, redirect, request, session, flash, send_file
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from io import BytesIO


# Configure Flask
app = Flask(__name__)

# Configure uploads
app.config['UPLOAD_FOLDER'] = "static/uploads/schedule"

# Max upload size in bytes (40 MB)
app.config['MAX_CONTENT_PATH'] = "40000000"


# Use filesystem instead of cookies
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Logs the user in and starts a session. Also sets user as standard or admin
@app.route("/login", methods=["GET", "POST"])
def login():
    
    if request.method == "POST":
        
        # Gets user input from form
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Checks for input
        if not email:
            flash("Enter an email address", "error")
            return render_template("login.html")
        
        if not password:
            flash("Enter your password", "error")
            return render_template("login.html")
        
        # Looks for email in user database
        db_lookup = get_user(email)
        
        # Handles if email not found
        if not db_lookup:
            flash("Email is not recognized", "error")
            return render_template("login.html")
        
        # Need to hash password etc
        if not check_password_hash(db_lookup[1], password):
            flash("Incorrect password", "error")
            return render_template("login.html")
        else:
            # Starts session (user_id is the email, user type is type)
            session['user_id'] = db_lookup[0]
            session['user_type'] = db_lookup[2]
            return redirect("/")
    return render_template("login.html")

# Registers user, if their email has been added to DB by an admin
@app.route("/register", methods=["GET", "POST"])
def register():
    
    if request.method == "POST":
        
        # Get form inputs
        email = request.form.get("email")
        name = request.form.get("name")
        password = request.form.get("password")

        # Validate inputs
        if not email:
            flash("Enter an email address", "error")
            return render_template("register.html")
        
        if not name:
            flash("Enter your name", "error")
            return render_template("register.html")
        
        if not password:
            flash("Enter a password", "error")
            return render_template("register.html")
        
        elif len(password) < 4:
            flash("Password must be longer than 4 characters", "error")
            return render_template("register.html")
        
        # Look email up in DB
        db_email = get_user(email)

        if not db_email:
            flash("Email not found", "error")
            return render_template("register.html")
        
        # Checks if they have set a password yet
        elif db_email[1]:
            flash("User already exists", "error")
            return render_template("register.html")
        
        # Hash password
        hash = generate_password_hash(password)

        # Name to lowercase
        name = name.lower()

        # Update name & hash where email matches
        register_user(name, hash, email)

        flash("Succesfully registered!", "green")

        return redirect("/")
    return render_template("register.html")

# Logs out the current user, and clears any session data
@app.route("/logout")
def logout():
    
    # Clears current session data
    session.clear()

    # Redirects to login
    return redirect("/")

@app.route("/scheduleview/<string:file_name>")
@login_required
def scheduleview(file_name):
    
    if file_name:
        
        if file_name == "not_available":
            flash("Not currently available", "error")
            return redirect("/")
        
        path = "/static/uploads/schedule/" + file_name
        return redirect(path)
    
    else:
        
        return redirect("/")

# Allows user to download files
@app.route("/download/<string:dl_id>")
@login_required
def download(dl_id):
    
    if dl_id:
        
        path = os.getcwd() + "/static/downloads/" + dl_id

        return send_file(path, dl_id, as_attachment=True)
    
    else:
        
        return redirect("/documents")


# Shows the schedule
@app.route("/")
@login_required
def index():
    #Today
    today_schedule = schedule_today()
    #Week
    week_schedule = schedule_week()
    if week_schedule is None:
        week_schedule = ("not_available",)
    
    if today_schedule is None:
        today_schedule = ("not_available",)

    return render_template("index.html", today_schedule=today_schedule, week_schedule=week_schedule)

# Shows the casting
@app.route("/casting")
@login_required
def casting():
    casting = get_casting()

    return render_template("casting.html", casting=casting)

# Looks for file by id, reads the binary, returns it as a file to user
@app.route("/casting/<id>")
@login_required
def show_casting(id):
    file = get_casting_file(id)
    new_file = BytesIO(file[0])
    return send_file(new_file, download_name=file[1], as_attachment=True)

# Brings up the yearly planner
@app.route("/planner")
@login_required
def planner():
    
    return redirect("static/22_23_planner.pdf")

# Allows user to download documents
@app.route("/documents")
@login_required
def documents():
    
    return render_template("documents.html")

# Admin only control panel. Allows to add / remove schedule
@app.route("/admin")
@login_required_admin
def admin():
    castings = get_casting()
    return render_template("admin.html", castings=castings)

@app.route("/uploadschedule", methods=["POST"])
@login_required_admin
def uploadschedule():
    
    upload_file = request.files["schedulefile"]
    file_name = secure_filename(upload_file.filename)
    type = request.form.get("week")

    if upload_file:
        
        upload_file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))
      
        if type is not None:
            upload_schedule_is_week(file_name)
        
        elif type is None:
            upload_schedule(file_name)

        flash("Upload complete", "green")
        return redirect("/admin")
    
    else:
        flash("Upload error", "error")
        return redirect("/admin")

@app.route("/uploadcasting", methods=["POST"])
@login_required_admin
def uploadcasting():
    
    upload_file = request.files["castingfile"]

    if upload_file:
        
        data = upload_file.read()
        file_name = upload_file.filename
        
        if data:
            upload_casting(data, file_name)

        flash("Upload complete", "green")
        return redirect("/admin")
    else:
        flash("Upload error", "error")
        return redirect("/admin")
    
# Removes casting file entry from db
@app.route("/removecasting", methods=["POST"])
@login_required_admin
def removecasting():
    # Get id
    id = request.form.get("casting")
    if id:
        id = int(id)
        # Remove db entry passing the id
        remove_casting(id)
        
        flash("Casting removed", "green")
        return redirect("/admin")
    else:
        flash("No file selected, no changes made", "error")
        return redirect("/admin")


# Admin only control panel to add/remove/edit users
@app.route("/users")
@login_required_admin
def users():
    db_lookup = admin_get_users()
    # Pass current user to jinja to disable buttons
    current_user = session['user_id']
    print(current_user)

    return render_template("users.html", users=db_lookup, current_user=current_user)

# Changes user type e.g admin / standard
@app.route("/changeusertype", methods=["POST"])
@login_required_admin
def editusers():
    email = request.form.get("email")
    type = request.form.get("type")
    admin_change_user_type(email, type)
    flash("User type updated", "green")
    return redirect("/users")

# Resets a users password, allowing them to reregister with a new one
@app.route("/resetuserpassword", methods=["POST"])
@login_required_admin
def resetuserpassword():
    email = request.form.get("email")
    admin_reset_user_password(email)
    flash("User password reset", "green")
    return redirect("users")

# Removes a user
@app.route("/removeuser", methods=["POST"])
@login_required_admin
def removeuser():
    email = request.form.get("email")
    admin_remove_user(email)
    flash("User removed", "green")
    return redirect("/users")

# Adds a user, allowing them to register using that email address
@app.route("/adduser", methods=["POST"])
@login_required_admin
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