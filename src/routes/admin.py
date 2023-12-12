import os
from flask import Blueprint,flash, jsonify,render_template, send_file,url_for,session,redirect,request
from werkzeug.security import generate_password_hash,check_password_hash

from ..extensions import mongo
from ..helper import generate_token,verify_token,create_csv,extract_questions
from ..send_email import send_email_admin
from bson.objectid import ObjectId
import string , random

from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,FileField,IntegerField
from wtforms.validators import DataRequired,InputRequired
from werkzeug.utils import secure_filename

admin = Blueprint("admin",__name__,url_prefix="/admin")

gen_testCode = ''.join(random.sample(string.ascii_uppercase+string.digits,k=8))

class AddAudioForm(FlaskForm):
    test_code = StringField("Test code",validators=[DataRequired(),InputRequired()])
    time = IntegerField("Time (in minutes)",validators=[DataRequired(),InputRequired()],render_kw={"step":"10"})
    lab_session = IntegerField("Lab Session",validators=[DataRequired(),InputRequired()])
    audio_no = IntegerField("Audio number",validators=[DataRequired(),InputRequired()])
    audio_file = FileField("Audio File",validators=[InputRequired()])
    questions_file = FileField("Questions File",validators=[InputRequired()])
    submit = SubmitField("Submit")

def check_login():
    try:
        if session["adminUsername"] is not None:
            return True
    except:
        return False

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
    if check_login():
        return render_template("admin/dashboard.html",name=session['adminUsername'])
    else:
        return redirect(url_for("admin.login"))


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
    if check_login():
        testCode = gen_testCode
        form = AddAudioForm()
        if request.method == "POST":
            if form.validate_on_submit():
                test_code = str(form.test_code.data)
                test_time = str(form.time.data)
                lab_session = str(form.lab_session.data)
                audio_no = str(form.audio_no.data)
                # Saving the audio
                audio_file = request.files['audio_file']
                audio_filename = secure_filename(audio_file.filename)
                audio_file.save(os.path.join(os.path.abspath('Quiz-App/src/static/audios/'),audio_filename))
                # Saving the excel file
                questions_file = request.files['questions_file']
                questions_filename = secure_filename(questions_file.filename)
                questions_file.save(os.path.join(os.path.abspath('Quiz-App/src/static/questions/'),questions_filename))

                try:
                    mongo.db.testDetails.insert_one({
                    "test_code":test_code,
                    "audio_name":audio_filename,
                    "test_time": test_time,
                    "lab_session":lab_session,
                    "audio_no":audio_no,
                    "questions_filename":questions_filename
                })
                    questions = extract_questions(os.path.join(os.path.abspath('Quiz-App/src/static/questions/'),questions_filename))
                    mongo.db[test_code].insert_many(questions)
                    flash("Uploaded Successfully!")
                except Exception as e:
                    flash(e)
            #return redirect(url_for('admin.add_questions',testCode = test_code))
        return render_template("admin/addQDb.html",testCode = testCode ,form=form)
    else:
        return redirect(url_for("admin.login"))


@admin.route("/download/<testCode>/<Class>")
def download(testCode,Class):
    path = os.path.join(os.path.abspath("/admin_reports/"),f"{Class}_{testCode}_(test-report).csv")
    return send_file(path,as_attachment=True)

@admin.route("/logout",methods=['GET', 'POST'])
def logout():
    session.pop('adminUsername')
    return redirect(url_for("admin.login"))

@admin.route("/show_reports",methods=['GET', 'POST'])
def show_report():
    if check_login():
        if request.method == "POST":
            test_code = request.form['test_code']
            Class = request.form.get('class')
            fetched_result = list(mongo.db[f"{test_code}-result"].find({"class":Class},{"_id":0,"class":0,"test_code":0}))
            if fetched_result!=[]:
                filename = f"{Class}_{test_code}_(test-report).csv"
                create_csv(filename=filename,report_details=fetched_result)
                return render_template("admin/show_all_reports.html",result=fetched_result,testCode=test_code,Class=Class)
            else:
                return render_template("admin/show_all_reports.html",result="",testCode=test_code,Class=Class)
        return render_template("admin/show_all_reports.html")
    else:
        return redirect(url_for("admin.login"))

@admin.route("/test_details/<test_code>",methods=['GET', 'POST'])
def fetch_test_details(test_code):
    if check_login():
        print(test_code)
        fetch_testcodes = list(mongo.db.testDetails.find({},{'_id':0,"test_time":0,"lab_session":0,"audio_no":0}))
        available_testcodes=[i["test_code"] for i in fetch_testcodes]
        if test_code in available_testcodes:
            test_details = list(mongo.db.testDetails.find({"test_code":test_code},{'_id':0,"test_time":0,"lab_session":0,"audio_no":0}))
            fetch_test_questions = list(mongo.db[test_code].find({},{"_id":0}))
            return jsonify({"test_details":test_details,"questions":fetch_test_questions})
        return jsonify({"resp":"TESTCODE NOT FOUND"})
    else:
        return redirect(url_for('admin.login'))

@admin.route("/show_questions",methods=['GET', 'POST'])
def show_questions():
    if check_login():
        fetch_testcodes = list(mongo.db.testDetails.find({},{'_id':0,"test_time":0,"lab_session":0,"audio_no":0}))
        test_codes=[i["test_code"] for i in fetch_testcodes]
        fetch_first_test = list(mongo.db.testDetails.find({"test_code":test_codes[0]},{'_id':0,"test_time":0,"lab_session":0,"audio_no":0}))
        fetch_test_questions = list(mongo.db[fetch_first_test[0]["test_code"]].find({},{"_id":0}))
        return render_template("admin/show_questions.html",test_codes=test_codes,test_details=fetch_first_test,questions=fetch_test_questions)
    else:
        return redirect(url_for('admin.login'))