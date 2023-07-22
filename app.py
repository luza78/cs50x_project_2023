from helpers import (login_required, login_required_admin, get_user, register_user, admin_add_user,
                      admin_get_users, admin_remove_user, admin_change_user_type, admin_reset_user_password,
                        upload_casting, get_casting_file, get_casting, remove_casting, upload_schedule,
                          remove_schedule, upload_schedule_is_week, schedule_today, schedule_week,
                          is_valid_file_extension)

from flask import Flask, render_template, redirect, request, session, flash, send_file
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from io import BytesIO

# Configure Flask
app = Flask(__name__)

# Configure upload
app.config['UPLOAD_FOLDER'] = "/static/uploads/"
app.config['MAX_CONTENT_PATH'] = "40000000"
ALLOWED_EXTENSIONS = ('txt', 'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xls', 'xlsx')

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
            flash("Email is not recognized, make sure you are registered!", "error")
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
            flash("Email not found. Make sure you have been added to the system", "error")
            return render_template("register.html")
        
        # Checks if they have set a password yet
        elif db_email[1]:
            flash("User already exists", "error")
            return render_template("register.html")
        
        # Hash password + name to lowercase then register to db
        hash = generate_password_hash(password)
        name = name.lower()
        register_user(name, hash, email)
        flash("Succesfully registered!", "green")
        return redirect("/")
    
    return render_template("register.html")

# Logs out the current user, and clears any session data
@app.route("/logout")
def logout():
    # Clears current session data, redirect to index (which will redirect to login)
    session.clear()
    return redirect("/")

@app.route("/scheduleview/<string:file_name>")
@login_required
def scheduleview(file_name):
    # Make sure we got passed a name
    if file_name:
        if file_name == "not_available":
            flash("Not currently available", "error")
            return redirect("/")
        
        path = app.config['UPLOAD_FOLDER'] + 'schedule/' + file_name
        return redirect(path)
    
    else:
        return redirect("/")

# Allows user to download files
@app.route("/download/<string:dl_id>")
@login_required
def download(dl_id):
    # Sends user file based on the passed id
    if dl_id:
        path = os.getcwd() + '/static/downloads/' + dl_id
        return send_file(path, dl_id, as_attachment=True)
    else:
        return redirect("/documents")



@app.route("/")
@login_required
def index():
    '''Query db to give the latest schedule from / it can then be passed to view by buttons'''
    today_schedule = schedule_today()
    week_schedule = schedule_week()
    
    if week_schedule is None:
        week_schedule = ("not_available",)
    
    if today_schedule is None:
        today_schedule = ("not_available",)

    return render_template("index.html", today_schedule=today_schedule, week_schedule=week_schedule)

@app.route("/casting")
@login_required
def casting():
    '''Render casting page'''
    casting = get_casting()
    return render_template("casting.html", casting=casting)

@app.route("/casting/<id>")
@login_required
def show_casting(id):
    '''looks up file in db from id, returns blob in [0], name in [1]'''
    file = get_casting_file(id)
    if file:
        new_file = BytesIO(file[0])
        return send_file(new_file, download_name=file[1], as_attachment=True)
    else:
        flash("Cannot find file", "error")
        return redirect("/")

@app.route("/planner")
@login_required
def planner():
    '''Gives user the planner'''
    return redirect("static/22_23_planner.pdf")

@app.route("/documents")
@login_required
def documents():
    '''Allows user to download documents'''
    return render_template("documents.html")

'''Admin only control panel'''
@app.route("/admin")
@login_required_admin
def admin():
    '''Passing in variables to jinja to display items in db and dir'''
    # Makes path, query db casting, get schedule names from the directory
    path = os.getcwd() + app.config['UPLOAD_FOLDER'] + 'schedule/'
    print(path)
    castings = get_casting()
    schedules = os.listdir(path)
    return render_template("admin.html", castings=castings, schedules=schedules)

@app.route("/uploadschedule", methods=["POST"])
@login_required_admin
def uploadschedule():
    '''Get file, the name, and make sure our variable is not empty'''
    upload_file = request.files["schedulefile"]
    file_name = secure_filename(upload_file.filename)
    
    if file_name:
        # Validate file extension
        if not (is_valid_file_extension(file_name, ALLOWED_EXTENSIONS)):
            flash("Invalid filetype. Valid types = .pdf .doc(x) .xls(x) .txt .jpg .jpeg .png", "error")
            return redirect("/admin")
        
        # Determine if its weekly or daily
        type = request.form.get("week")
            
        # If we have file loaded into variable
        if upload_file:
            upload_file.save(os.getcwd() + app.config['UPLOAD_FOLDER'] + 'schedule/' + file_name)
        
            # Is upload weekly
            if type is not None:
                if upload_schedule_is_week(file_name):
                    flash(f"Upload of '{file_name}' succesful", "green")
                    return redirect("/admin")
            
            # Is upload daily
            elif type is None:
                if upload_schedule(file_name):
                    flash(f"Upload of '{file_name}' succesful", "green")
                    return redirect("/admin")
        
    # If file variable is empty
    else:
        flash("Select a file", "error")
        return redirect("/admin")
   
   # If filename already exists
    flash("File with that name already exists", "error")
    return redirect("/admin")
    
@app.route("/removeschedule", methods=["POST"])
@login_required_admin
def removeschedule():
    file = request.form.get("schedule")
    
    if file:
        path = os.getcwd() + app.config['UPLOAD_FOLDER'] + 'schedule/' + file
        print(path)
        os.remove(path)
        remove_schedule(file)
        
        flash(f"'{file}' Has been removed from schedules", "green")
        return redirect("/admin")
    
    else:
        flash("No file selected, no changes made", "error")
        return redirect("/admin")


@app.route("/uploadcasting", methods=["POST"])
@login_required_admin
def uploadcasting():
    '''Gets file, stores file name, validate file'''
    upload_file = request.files["castingfile"]

    if upload_file:
        file_name = upload_file.filename
        
        if not (is_valid_file_extension(file_name, ALLOWED_EXTENSIONS)):
            flash("Invalid filetype. Valid types = .pdf .doc(x) .xls(x) .txt .jpg .jpeg .png", "error")
            return redirect("/admin")
        
        # Reads upload into variable
        data = upload_file.read()
        
        # Make sure data is not None
        if data:
            if upload_casting(data, file_name):
                flash(f"Upload of '{file_name}' was succesful", "green")
                return redirect("/admin")
            else:
                flash("File with that name already exists", "error")
                return redirect("/admin")
        # if data did not read
        else:
            flash("Data error", "error")
            return redirect("/admin")
    else:
        flash("Select a file", "error")
        return redirect("/admin")
    
# Removes casting file entry from db
@app.route("/removecasting", methods=["POST"])
@login_required_admin
def removecasting():
    # Get id, name, and remove db entry by passing the id
    id = request.form.get("casting")
    if id:
        id = int(id)
        casting_name = get_casting_file(id)
        remove_casting(id)
        flash(f"Casting '{casting_name[1]} has been removed", "green")
        return redirect("/admin")
    else:
        flash("No file selected, no changes made", "error")
        return redirect("/admin")


'''Admin only control panel to add/remove/edit users'''
@app.route("/users")
@login_required_admin
def users():
    # Pass current user to jinja to disable buttons
    db_lookup = admin_get_users()
    current_user = session['user_id']
    return render_template("users.html", users=db_lookup, current_user=current_user)

# Changes user type e.g admin / standard
@app.route("/changeusertype", methods=["POST"])
@login_required_admin
def editusers():
    email = request.form.get("email")
    type = request.form.get("type")
    admin_change_user_type(email, type)
    flash(f"User '{email}' changed to {type}", "green")
    return redirect("/users")

# Resets a users password, allowing them to reregister with a new one
@app.route("/resetuserpassword", methods=["POST"])
@login_required_admin
def resetuserpassword():
    email = request.form.get("email")
    admin_reset_user_password(email)
    flash(f"{email}'s password has been reset", "green")
    return redirect("users")

# Removes a user
@app.route("/removeuser", methods=["POST"])
@login_required_admin
def removeuser():
    email = request.form.get("email")
    admin_remove_user(email)
    flash(f"Removed {email} from users", "green")
    return redirect("/users")

'''Adds a user, allowing them to register using that email address'''
@app.route("/adduser", methods=["POST"])
@login_required_admin
def adduser():
    email = request.form.get("email")
    type = request.form.get("type")

    # Validate email: if it's longer than 4 characters. Also looks if input string has '@' and a '.' on right of the '@'
    if not email or len(email) < 4 or '@' and '.' not in email.rsplit('@', 1)[1]:
        flash("Enter a valid email address", "error")
        return redirect("/users")
    
    if not type:
        flash("Type select error", "error")
        return redirect("/users")
    
    # Check email address is available
    db_lookup = get_user(email)
    if db_lookup:
        flash(f"The '{email}' already in use", "error")
        return redirect("/users")
    else:
        admin_add_user(email, type)
        flash(f"'{email}' has been added to users", "green")
        return redirect("/users")

if __name__ == "__main__":
    app.run(debug=True)