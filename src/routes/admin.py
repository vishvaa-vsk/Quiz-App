import os
from flask import Blueprint,flash,render_template,url_for,session,redirect,request,jsonify
from werkzeug.security import generate_password_hash,check_password_hash

from ..extensions import mongo
from ..helper import generate_token,verify_token,send_email_admin
from bson.objectid import ObjectId
import string , random

from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,FileField
from wtforms.validators import DataRequired,InputRequired,regexp
from werkzeug.utils import secure_filename

admin = Blueprint("admin",__name__,url_prefix="/admin")

gen_testCode = ''.join(random.sample(string.ascii_uppercase+string.digits,
    k=8))

class AddAudioForm(FlaskForm):
    test_code = StringField("Enter the test code",validators=[DataRequired()])
    audio_file = FileField("Audio File",validators=[InputRequired()])
    submit = SubmitField("Submit")




@admin.route("/",methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        session.permanent=True
        username,passwd = request.form["adminName"],request.form["adminPass"]
        if mongo.db.admin.find_one({"username":username}):
            storedPasswd = mongo.db.admin.find_one({"username":username})["passwd"]
            if check_password_hash(storedPasswd,passwd):
                session["adminUsername"] = username
                return redirect(url_for('admin.dashboard'))
            flash("Username or password incorrect")
        else:
            flash("Username or password doesn't exist!")
    return render_template("admin/index.html")

@admin.route("/signup",methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        username,email,passwd,repasswd = request.form["adminName"],request.form['adminEmail'],request.form['adminPass'],request.form['adminRePass']
        user = mongo.db.users
        if not user.find_one({'username':username}) and not user.find_one({'email':email}):
            if not mongo.db.admin.find_one({"username":username}):
                if passwd == repasswd:
                    hased_value = generate_password_hash(passwd,method='scrypt')
                    try:
                        addAdmin = {"username":username,
                        "email":email,
                        "passwd":hased_value}
                        mongo.db.admin.insert_one(addAdmin)
                        flash("Registered successfully!")
                        return redirect(url_for('admin.login'))
                    except Exception as e:
                        flash(e)       
                else:
                    flash("Password doesn't match!")
            else:
                flash("User is already exists")
        else:
            flash("You are a student, you can't be a admin!")
    return render_template("admin/signup.html")

@admin.route("/dashboard",methods=['GET', 'POST'])
def dashboard():
    return "<h1>Admin Dashboard!</h1>"


@admin.route('/reset_request',methods=['GET', 'POST'])
def reset_request():
    if request.method == "POST":
        email = request.form['resetEmail']
        user = mongo.db.admin.find_one({"email":email})
        forgot_users = mongo.db.forgot_users
        if user:
            token = generate_token(userId=str(user['_id']))
            send_email_admin(userEmail=email,token=token,username=user['username'])
            flash("A link has been send to your email for password reset! click that to reset your password")
            if not forgot_users.find_one({"token":token}):
                forgot_users.insert_one({"token":token,"userId":user['_id']})
    return render_template('admin/resetEmail.html')

@admin.route("/verify_admin_reset/<token>",methods=['GET', 'POST'])
def reset_admin_password_verify(token):
    userId = mongo.db.forgot_users.find_one({'token':token})['userId']
    if userId is not None:
        try:
            if verify_token(token=token,userId=userId):
                return redirect(url_for("admin.reset_password",userId=userId))
        except:
            return "<center><h1>Invalid or expired token</h1></center>"
    else:
        return "<center><h1>Invalid or expired token</h1></center>"
    
@admin.route("/password_reset/<userId>",methods=['GET', 'POST'])
def reset_password(userId):
    if request.method == "POST":
            passwd,repasswd = request.form['newPass'],request.form['newRePass']
            if passwd == repasswd:
                new_hashed_value = generate_password_hash(passwd,method='scrypt')
                try:
                    mongo.db.admin.update_one({'_id':ObjectId(userId)},{"$set":{"passwd":new_hashed_value}})
                    flash("Password Changed!")
                    mongo.db.forgot_users.delete_many({'userId':ObjectId(userId)})
                    return redirect(url_for("admin.login"))
                except Exception as e:
                    flash(e)
            else:
                flash("Password does not match!")
    return render_template("admin/resetPassword.html",userId=userId)

@admin.route("/get_testCode",methods=['GET', 'POST'])
def get_test_code():
    testCode = gen_testCode
    form = AddAudioForm()
    if request.method == "POST":
        if form.validate_on_submit():
            test_code = str(form.test_code.data)
            file = request.files['audio_file']
            filename = secure_filename(file.filename)
            file.save(os.path.join('src/static/audios',filename))
        return redirect(url_for('admin.add_questions',testCode = test_code))
    return render_template("admin/addQDb.html",testCode = testCode ,form=form)

@admin.route("/add_questions/<testCode>",methods=['GET', 'POST'])
def add_questions(testCode):
    if request.method == "POST":
        question_no,question,choice1,choice2,choice3,choice4,correct_answer, =request.form['question_no'],request.form['question'],request.form['choice1'],request.form['choice2'],request.form['choice3'],request.form['choice4'],request.form.get('choice_select')
        try:
            mongo.db[testCode].insert_one({
                "question_no":question_no,
                "question":question,
                "choice1":choice1,
                "choice2":choice2,
                "choice3":choice3,
                "choice4":choice4,
                "correct_ans":correct_answer
            })
        except:
            flash("Internal Error!")
        
    return render_template("admin/addQuiz.html",testCode = testCode)