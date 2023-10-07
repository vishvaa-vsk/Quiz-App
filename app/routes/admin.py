from flask import Blueprint,flash,render_template,url_for,session,redirect,request,jsonify
from werkzeug.security import generate_password_hash,check_password_hash

from ..extensions import mongo

admin = Blueprint("admin",__name__,url_prefix="/admin")

@admin.route("/",methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        session.permanent=True
        username,passwd = request.form["adminName"],request.form["adminPass"]
        if mongo.db.admin.find_one({"username":username}):
            storedPasswd = mongo.db.admin.find_one({"username":username})["passwd"]
            if check_password_hash(storedPasswd,passwd):
                session["username"] = username
                return redirect(url_for('admin.dashboard'))
        else:
            flash("Username or password doesn't exist!")
    return render_template("admin/index.html")

@admin.route("/signup",methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        username,email,passwd,repasswd = request.form["adminName"],request.form['adminEmail'],request.form['adminPass'],request.form['adminRePass']
        if not mongo.db.admin.find_one({"username":username}):
            if passwd == repasswd:
                hased_value = generate_password_hash(passwd,method='scrypt')
                try:
                    addAdmin = {"username":username,
                    "email":email,
                    "passwd":hased_value}
                    mongo.db.admin.insert_one(addAdmin)
                    flash("Registered successfully!")
                except Exception as e:
                    flash(e)
            else:
                flash("Password doesn't match!")
    return render_template("admin/signup.html")

@admin.route("/dashboard",methods=['GET', 'POST'])
def dashboard():
    return "<h1>Admin Dashboard!</h1>"