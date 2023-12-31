import os
from flask import Blueprint,flash,render_template,url_for,session,redirect,request,jsonify,send_file
from werkzeug.security import generate_password_hash,check_password_hash
from ..extensions import mongo
from ..helper import generate_token,verify_token,create_report
from bson.objectid import ObjectId
from ..send_email import send_reset_email
import pdfkit
from ..send_email import send_report

main = Blueprint("main",__name__)

def check_login():
    try:
        if session["user_id"] is not None:
            return True
    except:
        return False

@main.route("/",methods=["GET","POST"])
def login():
    if request.method == "POST":
        session.permanent=True
        regno,passwd = request.form["studRegno"],request.form["studPass"]
        if mongo.db.users.find_one({"regno":regno}):
            storedPasswd = mongo.db.users.find_one({"regno":regno})["passwd"]
            user_id = ObjectId(mongo.db.users.find_one({"regno":regno})['_id'])
            username = mongo.db.users.find_one({"regno":regno})['username']
            if check_password_hash(storedPasswd,passwd):
                session["username"] = username
                session["user_id"] = str(user_id)
                return redirect(url_for('main.dashboard'))
            else:
                flash("Username or password incorrect")
        else:
            flash("Username or password doesn't exist!")
    return render_template("index.html")


@main.route("/studSignup",methods=["GET","POST"])
def signup():
    if request.method == "POST":
        username,Class,regno,passwd,repasswd,email = request.form["studName"],request.form['studClass'],request.form['studRegno'],request.form['studPass'],request.form['studRePass'],request.form['studEmail']
        if not mongo.db.users.find_one({"regno":regno}):
            if passwd == repasswd:
                hashed_value = generate_password_hash(passwd,method='scrypt')
                try:
                    addUser = {"username":username,"class":Class,"regno":regno,"email":email,"passwd":hashed_value}
                    mongo.db.users.insert_one(addUser)
                    flash("Register successful!")
                    return redirect(url_for("main.login"))
                except Exception as e:
                    flash(e)
            else:
                flash("Password doesn't match!")
        else:
            flash("User already exists")
    return render_template("signup.html")

@main.route('/home',methods=["GET","POST"])
def dashboard():
    if check_login():
        studName = session['username']
        return render_template('studentDashboard.html',studName=studName)
    else:
        return redirect(url_for('main.login'))


@main.route("/reset_request",methods=['GET', 'POST'])
def reset_request():
    if request.method == "POST":
        email = request.form['resetEmail']
        user = mongo.db.users.find_one({"email":email})
        forgot_users = mongo.db.forgot_users
        if user:
            token = generate_token(userId=str(user['_id']))
            send_reset_email(userEmail=email,token=token,username=user['username'])
            flash("A link has been send to your email for password reset! click that to reset your password")
            if not forgot_users.find_one({"token":token}):
                mongo.db.forgot_users.insert_one({"token":token,"userId":user['_id']})
    return render_template('resetEmail.html')

@main.route("/verify_reset/<token>",methods=['GET', 'POST'])
def reset_password_verify(token):
    try:
        userId = mongo.db.forgot_users.find_one({'token':token})['userId']
        if userId is not None:
            try:
                if verify_token(token=token,userId=userId):
                    return redirect(url_for("main.reset_password",userId=userId))
            except:
                return "<center><h1>Invalid or expired token</h1></center>"
        else:
            return "<center><h1>Invalid or expired token</h1></center>"
    except:
        return "<center><h1>Invalid or expired token</h1></center>"

@main.route("/password_reset/<userId>",methods=['GET', 'POST'])
def reset_password(userId):
    if request.method == "POST":
            passwd,repasswd = request.form['newPass'],request.form['newRePass']
            if passwd == repasswd:
                new_hashed_value = generate_password_hash(passwd,method='scrypt')
                try:
                    mongo.db.users.update_one({'_id':ObjectId(userId)},{"$set":{"passwd":new_hashed_value}})
                    flash("Password Changed!")
                    mongo.db.forgot_users.delete_many({'userId':ObjectId(userId)})
                    return redirect(url_for("main.login"))
                except Exception as e:
                    flash(e)
                    flash("Internal Error")
            else:
                flash("Password does not match!")
    return render_template("resetPassword.html",userId=userId)

@main.route("/verify_test/<testCode>",methods=['GET', 'POST'])
def verify_test(testCode):
    if request.method == "POST":
        if testCode in mongo.db.list_collection_names():
            return jsonify({'url':f'/test/{testCode}'})
    return "Redirecting to test!"

@main.route("/logout",methods=['GET', 'POST'])
def logout():
    session.pop('username')
    return redirect(url_for("main.login"))

@main.route("/test/<testCode>",methods=['GET', 'POST'])
def write_test(testCode):
    if check_login():
        if mongo.db[f"{testCode}-result"].find_one({'name':session["username"]}):
                return f"<h1> Hi {session['username']}, <br> You have already took this test! <br> Try checking your previous report..<br> Contact professors if you don't have an idea about this.."
        else:
            test_details = list(mongo.db[testCode].find({},{"_id":0,'correct_ans':0}))
            questions = list(mongo.db[testCode].find({},{"_id":0,"question_no":1,}))
            testdetails = mongo.db.testDetails.find_one({"test_code":testCode})
            correct_answers = list(mongo.db[testCode].find({},{"_id":0,"question_no":1,"correct_ans":1}))
            total_questions = []
            total_correct_answer = 0
            for i in questions:
                total_questions.append(int(i['question_no']))
        if request.method == "POST":
                try:
                    for j in total_questions:
                        user_answer = request.form[f"option-{j}"]
                        for i in correct_answers:
                            if str(i['question_no']) == str(j):
                                if str(i['correct_ans']) == str(user_answer):
                                    total_correct_answer+=1
                    percentage = (total_correct_answer/len(total_questions))*100
                    user = mongo.db.users.find_one({"_id":ObjectId(str(session['user_id']))})
                    add_user_result = {
                        '_id':ObjectId(str(session["user_id"])),
                        "name":session["username"],
                                 "class":user['class'],
                                 "regno":user["regno"],
                                 "teacher":user['teacher'],
                                "test_code":testCode,"score":(total_correct_answer/len(total_questions))*100,"percentage":percentage,
                                "status":"Pass" if percentage >= 50 else "Fail"}
                except Exception as e:
                    flash(e)
                    return jsonify({"error":e})
                try:
                    mongo.db[f"{testCode}-result"].insert_one(add_user_result)
                    return redirect(url_for('main.generate_report',testCode=testCode,name=session["username"]))
                except Exception as e:
                    flash(e)
                    flash("Internal error occured!")
        return render_template("showQuestions.html",testDetails=test_details,audio=testdetails['audio_name'],time=testdetails['test_time'])
    else:
        return redirect(url_for("main.login"))


@main.route("/download/<testCode>/<name>",methods=['GET', 'POST'])
def download(testCode,name):
    path = os.path.join(os.path.abspath("Quiz-App/reports"),f"{name}'s_{testCode}_report.pdf")
    return send_file(path,as_attachment=True)


@main.route("/previous_result",methods=['GET', 'POST'])
def get_previous_result():
    name = session["username"]
    if request.method == "POST":
        last_test = list(mongo.db.testDetails.find({},{"_id":0}))
        test_code = last_test[-1]['test_code']
        latest_result = mongo.db[f"{test_code}-result"].find_one({"name":name},{"_id":0})
        if latest_result is not None:
            return latest_result
    return jsonify({"testcode":"None","name":"None","score":"None","percentage":"None","status":"None"})

@main.route("/download_prev_result",methods=['GET', 'POST'])
def download_prev_result():
    if check_login():
        name = session["username"]
        if request.method == "POST":
            testCode = request.form["testCode"]
            if mongo.db[f"{testCode}-result"].find_one({"name":name}):
                try:
                    return download(testCode=testCode,name=name)
                except:
                    return "FILE NOT FOUND!"
        return render_template("previous_result.html",name=name)
    else:
        return redirect(url_for("main.login"))


@main.route("/report/<testCode>/<name>",methods=['GET', 'POST'])
def generate_report(testCode,name):
    if check_login():
        if mongo.db.users.find_one({"username":name}) and mongo.db[f"{testCode}-result"].find_one({'name':name}):
            testdetails = mongo.db.testDetails.find_one({"test_code":testCode})
            user_details = mongo.db.users.find_one({"username":name})
            user_test_report = mongo.db[f"{testCode}-result"].find_one({'name':name})

            email_template = create_report(
            name=name,testCode=testCode,class_and_sec=user_details['class'],regno=user_details['regno'],status=user_test_report['status'],score=user_test_report['score'],percentage=user_test_report['percentage'],lab_session=testdetails["lab_session"],audio_no=testdetails["audio_no"]
            ,file="report_base.html")

            template = create_report(
            name=name,testCode=testCode,class_and_sec=user_details['class'],regno=user_details['regno'],status=user_test_report['status'],score=user_test_report['score'],percentage=user_test_report['percentage'],lab_session=testdetails["lab_session"],audio_no=testdetails["audio_no"]
            ,file="report.html")
            filename = f"{name}'s_{testCode}_report.pdf"

            pdfkit.from_string(email_template,os.path.join(os.path.abspath("Quiz-App/reports"),filename))
            if os.path.isfile(os.path.join(os.path.abspath("Quiz-App/"),filename)):
                send_report(username=name,userEmail=user_details["email"],testCode=testCode,filename=filename)
                flash("The report has been delivered to your inbox!")
        return template
    else:
        return redirect(url_for('main.login'))

@main.route("/get_user_details",methods=['GET', 'POST'])
def get_user_details():
    if request.method == "POST":
        user_id = session.get("user_id")
        user_details = mongo.db.users.find_one({'_id':ObjectId(user_id)},{'_id':0})
        return user_details
    return "METHOD NOT ALLOWED"

@main.route("/edit_details",methods=['GET', 'POST'])
def edit_details():
    if check_login():
        if request.method == "POST":
            user_id = session.get("user_id")
            username,regno,Class,email,teacher = request.form["studName"],request.form["studRegno"],request.form["studClass"].upper(),request.form["studEmail"],request.form.get("teacherName")
            mongo.db.users.update_one({"_id":ObjectId(user_id)},{"$set":{"username":username,"regno":regno,"class":Class,"email":email,"teacher":teacher}})
        return render_template("edit_user_details.html",studName = session["username"])
    else:
        return redirect(url_for('main.login'))