from flask import Blueprint,flash,render_template,url_for,session,redirect,request,jsonify
from werkzeug.security import generate_password_hash,check_password_hash
import os
from os import path
import random
from dotenv import load_dotenv
from ..extensions import mongo , mail
from flask_mail import Message
import jwt
import datetime

main = Blueprint("main",__name__)

token_secret_key = os.environ.get("TOKEN_SECRET_KEY")

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(path.join(basedir,".env"))

otp = random.randint(100000,999999)

def generate_token(userId,expires=600):
    reset_token = jwt.encode(
        {'payload':f"{userId}",
         'exp':datetime.datetime.now(tz=datetime.timezone.utc)+datetime.timedelta(seconds=expires)},
         token_secret_key,
         algorithm="HS256")
    return reset_token

def verify_token(token,userId):
    try:
        data = jwt.decode(token,token_secret_key,leeway=datetime.timedelta(seconds=10),algorithms=["HS256"])
    except:
        return False
    if data.get('payload') == userId:
        return True


def send_email(token,userEmail):
    msg = Message('Password Reset Request',sender='testvec26@gmail.com',recipients=[userEmail],)
    msg.body = f'''To reset the password, visit the following link: {url_for('main.resetPassword',token=token,_external=True)}If you did not make this request then simply ignore this email!'''
    mail.send(msg)

    



@main.route("/",methods=["GET","POST"])
def login():
    if request.method == "POST":
        session.permanent=True
        username,passwd = request.form["studName"],request.form["studPass"]
        if mongo.db.users.find_one({"username":username}):
            storedPasswd = mongo.db.users.find_one({"username":username})["passwd"]
            if check_password_hash(storedPasswd,passwd):
                session["username"] = username
                print("Login successful")
                return redirect(url_for('main.dashboard'))
        else:
            flash("Username or password doesn't exist!")
    return render_template("index.html")


@main.route("/studSignup",methods=["GET","POST"])
def signup():
    if request.method == "POST":
        username,Class,regno,passwd,repasswd = request.form["studName"],request.form['studClass'],request.form['studRegno'],request.form['studPass'],request.form['studRePass']
        if not mongo.db.users.find_one({"username":username}):
            if passwd == repasswd:
                hased_value = generate_password_hash(passwd,method='scrypt')
                try:
                    addUser = {"username":username,"class":Class,"regno":regno,"passwd":hased_value}
                    mongo.mongo.users.insert_one(addUser)
                    flash("Register Successfull")
                    return redirect(url_for("main.login"))
                except Exception as e:
                    flash(e)
            else:
                flash("Password doesn't match!")
    return render_template("signup.html")

@main.route('/home',methods=["GET","POST"])
def dashboard():
    studName = session['username']
    return render_template('studentDashboard.html',studName=studName)

@main.route("/reset_request",methods=['GET', 'POST'])
def resetRequest():
    if request.method == "POST":
        email = request.form['resetEmail']
        user = mongo.db.users.find_one({"email":email})
        if user:
            token = generate_token(userId=user['_id'])
            send_email(userEmail = email,token=token)
            flash("A link has been send to your email for password reset! click that to reset your password")
            mongo.db.forgot_users.insert_one({
                "token":token,
                "userId":user['_id']
            })
    return render_template('resetEmail.html')

@main.route("/verify_reset/<token>",methods=['GET', 'POST'])
def resetPassword(token):
    if request.method == "POST":
        userId = mongo.db.forgot_user.find_one({'token':token})
        if verify_token(token=token,userId=userId):
            passwd,repasswd = request.form['Pass'],request.form['RePass']
            if passwd == repasswd:
                new_hased_value = generate_password_hash(passwd,method='scrypt')
                try:
                    mongo.db.users.update_one({'_id':userId},{'$set':{"passwd":new_hased_value}})
                    flash("Password Changed!")
                    mongo.db.forgot_user.delete_one({'userId':userId})
                except Exception as e:
                    flash(e)
            flash("Password does not match!")
        flash("Reset Link is invalid or expired!")
    return render_template("resetPassword.html")
        

    