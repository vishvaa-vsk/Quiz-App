import os,tempfile
from flask import Blueprint,flash,render_template,url_for,session,redirect,request,jsonify,send_file,make_response
from werkzeug.security import generate_password_hash,check_password_hash
from ..extensions import mongo
from ..helper import generate_token,verify_token,create_report,remove_duplicates
from bson.objectid import ObjectId
from ..send_email import send_reset_email
import pdfkit
from ..send_email import send_report

teacher = Blueprint("teacher",__name__,url_prefix="/teacher")

def check_login():
    try:
        if session["teacherName"] is not None:
            return True
    except:
        return False

@teacher.route("/",methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        session.permanent=True
        user_email,passwd = request.form["teacherEmail"],request.form["teacherPass"]
        if mongo.db.teachers.find_one({"email":user_email}):
            user_details = mongo.db.teachers.find_one({"email":user_email})
            storedPasswd = user_details["passwd"]
            if check_password_hash(storedPasswd,passwd):
                session["teacher_id"] = str(user_details["_id"])
                session["teacherName"] = user_details["username"]
                return redirect(url_for("teacher.dashboard"))
            flash("Username or password incorrect")
        else:
            flash("Username or password doesn't exist!")
    return render_template("teacher/index.html")

@teacher.route("/signup",methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        username,email,passwd,repasswd = request.form.get("teacherName"),request.form['teacherEmail'],request.form['teacherPass'],request.form['teacherRePass']
        user = mongo.db.users
        if not user.find_one({'username':username}) and not user.find_one({'email':email}):
            if not mongo.db.teachers.find_one({"username":username}):
                if passwd == repasswd:
                    hased_value = generate_password_hash(passwd,method='scrypt')
                    try:
                        addteacher = {"username":username,
                        "email":email,
                        "passwd":hased_value}
                        mongo.db.teachers.insert_one(addteacher)
                        flash("Registered successfully!")
                        return redirect(url_for('teacher.login'))
                    except Exception as e:
                        flash(e)
                else:
                    flash("Password doesn't match!")
            else:
                flash("User is already exists")
        else:
            flash("You are a student, you can't be a teacher!")
    return render_template("teacher/signup.html")

@teacher.route('/reset_request',methods=['GET', 'POST'])
def reset_request():
    if request.method == "POST":
        email = request.form['resetEmail']
        user = mongo.db.teachers.find_one({"email":email})
        forgot_users = mongo.db.forgot_users
        if user:
            token = generate_token(userId=str(user['_id']))
            send_reset_email(userEmail=email,token=token,username=user['username'])
            flash("A link has been send to your email for password reset! click that to reset your password")
            if not forgot_users.find_one({"token":token}):
                forgot_users.insert_one({"token":token,"userId":user['_id']})
    return render_template('teacher/resetEmail.html')

@teacher.route("/verify_teacher_reset/<token>",methods=['GET', 'POST'])
def reset_teacher_password_verify(token):
    userId = mongo.db.forgot_users.find_one({'token':token})['userId']
    if userId is not None:
        try:
            if verify_token(token=token,userId=userId):
                return redirect(url_for("teacher.reset_password",userId=userId))
        except:
            return "<center><h1>Invalid or expired token</h1></center>"
    else:
        return "<center><h1>Invalid or expired token</h1></center>"

@teacher.route("/password_reset/<userId>",methods=['GET', 'POST'])
def reset_password(userId):
    if request.method == "POST":
            passwd,repasswd = request.form['newPass'],request.form['newRePass']
            if passwd == repasswd:
                new_hashed_value = generate_password_hash(passwd,method='scrypt')
                try:
                    mongo.db.teachers.update_one({'_id':ObjectId(userId)},{"$set":{"passwd":new_hashed_value}})
                    flash("Password Changed!")
                    mongo.db.forgot_users.delete_many({'userId':ObjectId(userId)})
                    return redirect(url_for("teacher.login"))
                except Exception as e:
                    flash(e)
            else:
                flash("Password does not match!")
    return render_template("teacher/resetPassword.html",userId=userId)

@teacher.route("/dashboard",methods=['GET', 'POST'])
def dashboard():
    if check_login():
        return render_template("teacher/dashboard.html",name=session['teacherName'])
    else:
        return redirect(url_for("teacher.login"))

@teacher.route("/logout",methods=['GET', 'POST'])
def logout():
    session.pop('teacherName')
    session.pop('teacher_id')
    return redirect(url_for("teacher.login"))

@teacher.route("/test_details/<testCode>",methods=['GET', 'POST'])
def fetch_test_details(testCode):
    if check_login():
        fetch_testcodes = list(mongo.db.testDetails.find({},{'_id':0,"test_time":0}))
        raw_available_testcodes=[i["test_code"] for i in fetch_testcodes]
        available_testcodes = remove_duplicates(raw_available_testcodes)
        if testCode in available_testcodes:
            test_details = list(mongo.db.testDetails.find({"test_code":testCode},{'_id':0,"test_time":0}))
            fetch_test_questions = list(mongo.db[testCode].find({},{"_id":0,"correct_ans":0}))
            return render_template("teacher/show_questions.html",test_codes=available_testcodes,test_details=test_details,questions=fetch_test_questions)
        return jsonify({"resp":"TESTCODE NOT FOUND"})
    else:
        return redirect(url_for('teacher.login'))

@teacher.route("/show_questions",methods=['GET', 'POST'])
def show_questions():
    if check_login():
        fetch_testcodes = list(mongo.db.testDetails.find({},{'_id':0,"test_time":0}))
        raw_test_codes=[i["test_code"] for i in fetch_testcodes]
        test_codes = remove_duplicates(raw_test_codes)
        fetch_first_test = list(mongo.db.testDetails.find({"test_code":test_codes[0]},{'_id':0,"test_time":0}))
        fetch_test_questions = list(mongo.db[fetch_first_test[0]["test_code"]].find({},{"_id":0,"correct_ans":0}))
        return render_template("teacher/show_questions.html",test_codes=test_codes,test_details=fetch_first_test,questions=fetch_test_questions)
    else:
        return redirect(url_for('teacher.login'))
    
@teacher.route("/issues/<testCode>",methods=['GET', 'POST'])
def fetch_technical_issues(testCode):
    if check_login():
        fetch_testcodes = list(mongo.db.testDetails.find({},{"test_code":1}))
        raw_available_testcodes=[i["test_code"] for i in fetch_testcodes]
        available_testcodes = remove_duplicates(raw_available_testcodes)
        if testCode in available_testcodes:
            zero_results = list(mongo.db[f"{testCode}-result"].find({"score":0}))
            return render_template("teacher/technical_issues.html",test_codes=available_testcodes,zero_results=zero_results)
        return jsonify({"resp":"TESTCODE NOT FOUND"})
    else:
        return redirect(url_for('teacher.login'))


@teacher.route("/technical_issues",methods=['GET', 'POST'])
def technical_issues():
    if check_login():
        fetch_testcodes = list(mongo.db.testDetails.find({},{"test_code":1}))
        raw_test_codes=[i["test_code"] for i in fetch_testcodes]
        test_codes = remove_duplicates(raw_test_codes)
        zero_results = list(mongo.db[f"{test_codes[0]}-result"].find({"score":0},{}))
        return render_template("teacher/technical_issues.html",test_codes=test_codes,zero_results=zero_results)
    else:
        return redirect(url_for("teacher.login"))
    
@teacher.route("/delete_result",methods=['GET', 'POST'])
def delete_result():
    if check_login():
        if request.method == "POST":
            obj_id = request.json["obj_id"]
            test_code = request.json["test_code"]
            try:
                mongo.db[f"{test_code}-result"].delete_one({"_id":ObjectId(obj_id)})
                flash("Deleted successfully!")
                return jsonify({"url":f"/teacher/issues/{test_code}"})
            except Exception as e:
                flash(e)
        return redirect(url_for("teacher.technical_issues"))
    else:
        return redirect(url_for("teacher.login"))

@teacher.route("/view_results",methods=['GET', 'POST'])
def view_results():
    if check_login():
        fetch_testcodes = list(mongo.db.testDetails.find({},{'_id':0,"test_time":0}))
        raw_test_codes=[i["test_code"] for i in fetch_testcodes]
        test_codes = remove_duplicates(raw_test_codes)
        try:
            handling_classes = mongo.db.teachers.find_one({"username":session["teacherName"]})["handling_classes"]
            classes = [i[j] for i in handling_classes for j in range(len(i))]
        except:
            classes = []
        if request.method == "POST":
            testCode = request.form.get("test_code")
            Class = request.form.get("classes")
            test_results = list(mongo.db[f"{testCode}-result"].find({"$and":[{"teacher":session.get("teacherName")},{"class":Class}]}).sort("regno",1))
            return render_template("teacher/view_reports.html",test_codes=test_codes,classes=classes,test_results=test_results,Class=Class,test_code=testCode)
        return render_template("teacher/view_reports.html",test_codes=test_codes,classes=classes)
    else:
        return redirect(url_for("teacher.login"))

# @teacher.route("/delete_class",methods=['GET', 'POST'])
# def delete_class():
#     if check_login():
#         if request.method == "POST":
#             section = request.json["section"]
#             try:
#                 print(section)
#                 mongo.db.teachers.update_one({"username":session["teacherName"]},{"$pull":{"handling_classes":section}})
#                 flash("Deleted successfully!")
#                 return jsonify({"url":"/teacher/handling_classes"})
#             except Exception as e:
#                 print(e)
#         return redirect(url_for("teacher.add_handling_classes"))
#     else:
#         return redirect(url_for('teacher.login'))

@teacher.route("/add_classes",methods=['GET', 'POST'])
def add_classes():
    Class = request.json["class"]
    handling_classes = []
    handling_classes.append(Class)
    print(handling_classes)
    try:
        if mongo.db.teachers.find_one({"$and":[{"username":session["teacherName"]},{"handling_classes":{"$exists":True}}]}):
            mongo.db.teachers.update_one({"username":session["teacherName"]},{"$push":{"handling_classes":handling_classes}})
        else:
            mongo.db.teachers.update_one({"username":session["teacherName"]},{"$push":{"handling_classes":handling_classes}})
    except Exception as e:
        print(e)
    return jsonify({"url":f"/teacher/handling_classes"})

@teacher.route("/handling_classes",methods=['GET', 'POST'])
def add_handling_classes():
    if check_login():
        try:
            handling_classes = mongo.db.teachers.find_one({"username":session["teacherName"]})["handling_classes"]
            classes = [i[j] for i in handling_classes for j in range(len(i))]
        except:
            classes=[]
        return render_template("teacher/add_handling_classes.html",Class=classes)
    else:
        return redirect(url_for('teacher.login'))