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
    """
    The function `check_login` attempts to verify if a user is logged in by checking if a user ID is
    stored in the session.
    :return: The function `check_login()` is returning a boolean value. If the `session["user_id"]` is
    not None, it will return `True`. Otherwise, it will return `False`.
    """
    try:
        if session["user_id"] is not None:
            return True
    except:
        return False

@main.route("/",methods=["GET","POST"])
def login():
    """
    This Python function handles user login authentication using Flask and MongoDB.
    :return: The code snippet provided is a Flask route function for handling login functionality. If
    the request method is POST, it checks the user credentials against the stored password in the
    database. If the credentials are correct, it sets session variables for the username and user ID and
    redirects to the dashboard. If the credentials are incorrect, it flashes a message indicating the
    issue.
    """
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
    """
    The `signup` function in Python handles user registration by checking if the user already exists,
    validating password match, hashing the password, and adding the user to the database if all
    conditions are met.
    :return: The `signup()` function returns either a rendered template "signup.html" if the request
    method is not "POST", or it redirects to the "main.login" route after processing the form data if
    the request method is "POST".
    """
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
    """
    The `dashboard` function checks if a user is logged in and renders the student dashboard with the
    student's name, or redirects to the login page if not logged in.
    :return: If the user is logged in, the function will return the rendered template
    'studentDashboard.html' with the student's name passed as a parameter. If the user is not logged in,
    the function will redirect to the login page.
    """
    if check_login():
        studName = session['username']
        return render_template('studentDashboard.html',studName=studName)
    else:
        return redirect(url_for('main.login'))


@main.route("/reset_request",methods=['GET', 'POST'])
def reset_request():
    """
    The `reset_request` function handles a POST request to reset a user's password by sending a reset
    email with a unique token and storing the token in the database for verification.
    :return: The function `reset_request` is returning the rendered template 'resetEmail.html'.
    """
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
    """
    The function `reset_password_verify` checks if a token is valid and redirects to the reset password
    page if it is, otherwise it displays an error message.

    :param token: The `token` parameter in the `reset_password_verify` function is used to verify the
    user's request to reset their password. The function checks if the token is valid and not expired
    before allowing the user to proceed with resetting their password
    :return: The function `reset_password_verify(token)` returns either a redirect to the
    "reset_password" route with the userId parameter if the token is verified, or it returns a message
    "<center><h1>Invalid or expired token</h1></center>" if the token is invalid or expired.
    """
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
    """
    The `reset_password` function in Python handles resetting a user's password by updating it in the
    database after verifying the new password matches the confirmation.

    :param userId: The `userId` parameter in the `reset_password` function is used to identify the user
    for whom the password is being reset. It is likely an identifier, such as a unique user ID or
    username, that is used to locate the user in the database and update their password
    :return: the rendered template "resetPassword.html" with the userId parameter passed to it.
    """
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
    """
    The function `verify_test` checks if a POST request contains a specific test code in a MongoDB
    collection and returns a JSON response with a URL if the code exists.

    :param testCode: The `testCode` parameter in the `verify_test` function seems to represent a code
    that is being checked against a list of collection names in a MongoDB database. If the `testCode` is
    found in the list of collection names, the function returns a JSON response with a URL pointing to
    the
    :return: "Redirecting to test!"
    """
    if request.method == "POST":
        if testCode in mongo.db.list_collection_names():
            return jsonify({'url':f'/test/{testCode}'})
    return "Redirecting to test!"

@main.route("/logout",methods=['GET', 'POST'])
def logout():
    """
    The `logout` function removes the 'username' from the session and redirects the user to the login
    page.
    :return: The `logout` function is returning a redirect response to the "login" route of the "main"
    blueprint.
    """
    session.pop('username')
    return redirect(url_for("main.login"))

@main.route("/test/<testCode>",methods=['GET', 'POST'])
def write_test(testCode):
    """
    The `write_test` function in Python checks if a user is logged in, retrieves test questions, allows
    users to submit answers, calculates the percentage score, and stores the result in a MongoDB
    collection.

    :param testCode: The `testCode` parameter in the `write_test` function is used to identify the
    specific test for which the user wants to write a test. It is used to fetch questions, details, and
    correct answers related to that particular test from the database. The function checks if the user
    is logged in
    :return: The function `write_test` returns either a HTML message indicating that the user has
    already taken the test or it renders a template with questions for the test if the user is logged
    in. If the request method is POST, it processes the user's answers, calculates the percentage score,
    and inserts the user's test result into the database. Finally, it redirects the user to generate a
    report for the test
    """
    if check_login():
        if mongo.db[f"{testCode}-result"].find_one({'name':session["username"]}):
                return f"<h1> Hi {session['username']}, <br> You have already took this test! <br> Try checking your previous report..<br> Contact professors if you don't have an idea about this..</h1>"
        else:
            questions = list(mongo.db[testCode].find({},{"_id":0,'correct_ans':0}))
            sorted_questions = sorted(questions, key=lambda x: x['question_no'])
            question_nos = list(mongo.db[testCode].find({},{"_id":0,"question_no":1,}))
            testdetails = mongo.db.testDetails.find_one({"test_code":testCode})
            test_type = testdetails["test_type"]
            correct_answers = list(mongo.db[testCode].find({},{"_id":0,"question_no":1,"correct_ans":1}))
            total_questions = []
            total_correct_answer = 0
            for i in question_nos:
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
                try:
                    mongo.db[f"{testCode}-result"].insert_one(add_user_result)
                    if test_type != "value added":
                        return redirect(url_for('main.generate_report',testCode=testCode,name=session["username"]))
                    else:
                        return redirect(url_for('main.generate_certificate',testCode=testCode,name=session["username"]))
                except Exception as e:
                    flash(e)
                    flash("Internal error occurred!")
        return render_template("showQuestions.html",testDetails=sorted_questions,audio=testdetails['audio_name'],time=testdetails['test_time'])
    else:
        return redirect(url_for("main.login"))

@main.route("/univ_exam",methods=['GET', 'POST'])
def univ_exam():
    """
    The `univ_exam` function returns a rendered template for a university exam page with the student's
    name passed as a parameter.
    :return: The function `univ_exam()` is returning a call to the `render_template()` function with the
    parameters "univ_exam.html" and "studName = session.get("username")".
    """
    return render_template("univ_exam.html",studName = session.get("username"))

@main.route("/verify_univ_test/<testCode>",methods=['GET', 'POST'])
def verify_univ_test(testCode):
    """
    It seems like you have pasted a code snippet for a function named `verify_univ_test`, but it appears
    to be incomplete. How can I assist you with this function?

    :param testCode: It seems like you were about to provide some information about the `testCode`
    parameter in the `verify_univ_test` function. Could you please provide more details or let me know
    how I can assist you further with this function?
    """
    if request.method == "POST":
        if testCode in mongo.db.list_collection_names():
            if mongo.db.testDetails.find_one({"test_code":testCode})["test_type"]=="University Exam":
                return jsonify({'url':f'/univ_test/{testCode}'})
    return "Redirecting to test!"

@main.route("/univ_test/<testCode>",methods=['GET', 'POST'])
def write_univ_test(testCode):
    """
    This Python function is designed to handle writing university tests, including checking if a user
    has already taken the test, processing user answers, and storing the results in a MongoDB database.

    :param testCode: The `testCode` parameter is used to identify a specific test within the system. It
    is used to retrieve test questions, details, and results related to that particular test
    :return: The function `write_univ_test` returns different responses based on certain conditions. If
    the user is not logged in, it will redirect to the login page. If the user is logged in, it will
    check if the user has already taken the test. If the user has already taken the test, it will
    display a message indicating that the user has already taken the test. If the user has not
    """
    if check_login():
        if mongo.db[f"{testCode}-result"].find_one({'name':session["username"]}):
                return f"<h1> Hi {session['username']}, <br> You have already took this test! <br> Try checking your previous report..<br> Contact professors if you don't have an idea about this..</h1>"
        else:
            questions = list(mongo.db[testCode].find({},{"_id":0,'correct_ans':0}))
            question_nos = list(mongo.db[testCode].find({},{"_id":0,"question_no":1,}))
            sorted_questions = sorted(questions, key=lambda x: x['question_no'])
            testdetails = mongo.db.testDetails.find_one({"test_code":testCode})
            test_type = testdetails["test_type"]
            correct_answers = list(mongo.db[testCode].find({},{"_id":0,"question_no":1,"correct_ans":1}))
            total_questions = []
            total_correct_answer = 0
            for i in question_nos:
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
                                 "test_type":test_type,
                                "test_code":testCode,"score":(total_correct_answer/len(total_questions))*100,"percentage":percentage,
                                "status":"Pass" if percentage >= 50 else "Fail"}
                except Exception as e:
                    flash(e)
                try:
                    mongo.db[f"{testCode}-result"].insert_one(add_user_result)
                    return render_template("redirect_home.html",studName=session.get("username"))
                except Exception as e:
                    flash(e)
                    flash("Internal error occurred!")
        return render_template("showQuestions.html",testDetails=sorted_questions,audio=testdetails['audio_name'],time=testdetails['test_time'])
    else:
        return redirect(url_for("main.login"))

@main.route("/download/<testCode>/<name>",methods=['GET', 'POST'])
def download(testCode,name):
    """
    The function `download` generates a file path for a PDF report based on the test code and name, and
    then sends the file for download.

    :param testCode: The `testCode` parameter is likely a unique identifier or code associated with a
    specific test or quiz. It is used to generate a customized report file for the test taker
    :param name: The `name` parameter in the `download` function represents the name of the user for
    whom the report is being generated. It is used to create a unique filename for the report by
    incorporating the user's name in the file name
    :return: The function `download` is returning the file located at the specified `path` as an
    attachment for download.
    """
    path = os.path.join(os.path.abspath("Quiz-App/reports"),f"{name}'s_{testCode}_report.pdf")
    return send_file(path,as_attachment=True)


@main.route("/previous_result",methods=['GET', 'POST'])
def get_previous_result():
    name = session["username"]
    if request.method == "POST":
        last_test = list(mongo.db.testDetails.find({},{"_id":0}))
        test_code = last_test[-1]['test_code']
        latest_result = mongo.db[f"{test_code}-result"].find_one({"$and":[{"name":name},{"test_type":{"$ne":"University Exam"}}]},{"_id":0})
        if latest_result is not None:
            return latest_result
    return jsonify({"testcode":"None","name":"None","score":"None","percentage":"None","status":"None"})

@main.route("/download_prev_result",methods=['GET', 'POST'])
def download_prev_result():
    """
    The function `download_prev_result` checks if a user is logged in, downloads a test result if
    conditions are met, and generates a report if needed.
    :return: either a PDF file download of a test report or rendering the "previous_result.html"
    template based on certain conditions.
    """
    if check_login():
        name = session["username"]
        if request.method == "POST":
            testCode = request.form["testCode"]
            if mongo.db.testDetails.find_one({"test_code":testCode})["test_type"]!="University Exam" and mongo.db[f"{testCode}-result"].find_one({"name":name}):
                try:
                    return download(testCode=testCode,name=name)
                except:
                    testdetails = mongo.db.testDetails.find_one({"test_code":testCode})
                    user_details = mongo.db.users.find_one({"username":name})
                    user_test_report = mongo.db[f"{testCode}-result"].find_one({'name':name})
                    report = create_report(name=name,testCode=testCode,class_and_sec=user_details['class'],regno=user_details['regno'],status=user_test_report['status'],score=user_test_report['score'],percentage=user_test_report['percentage'],lab_session=testdetails["lab_session"],audio_no=testdetails["audio_no"]
            ,file="report_base.html")
                    filename = f"{name}'s_{testCode}_report.pdf"
                    pdfkit.from_string(report,os.path.join(os.path.abspath("Quiz-App/reports"),filename))
                    return download(testCode=testCode,name=name)
            else:
                flash("University Results can't be downloaded")
        return render_template("previous_result.html",name=name)
    else:
        return redirect(url_for("main.login"))


@main.route("/report/<testCode>/<name>",methods=['GET', 'POST'])
def generate_report(testCode,name):
    """
    The function `generate_report` generates a test report for a user based on their test code and name,
    and sends the report via email.

    :param testCode: The `testCode` parameter in the `generate_report` function seems to represent a
    unique identifier for a specific test. It is used to retrieve test details and results from the
    database related to that particular test. This code snippet appears to be part of a web application
    that generates and sends reports to users
    :param name: The `name` parameter in the `generate_report` function is used to specify the username
    for which the report is being generated. This username is used to retrieve user details and test
    results from the database in order to generate the report
    :return: The function `generate_report` returns either the `template` variable or the string "REPORT
    NOT FOUND".
    """
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
            if os.path.isfile(os.path.join(os.path.abspath("Quiz-App/reports"),filename)):
                send_report(username=name,userEmail=user_details["email"],testCode=testCode,filename=filename)
                flash("The report has been delivered to your inbox!")
            return template
        return "REPORT NOT FOUND"
    else:
        return redirect(url_for('main.login'))

@main.route("/generate_certificate/<testCode>/<name>",methods=['GET','POST'])
def generate_certificate(testCode,name):
    pass
#     if check_login():
#         if mongo.db.users.find_one({"username":name}) and mongo.db[f"{testCode}-result"].find_one({'name':name}):
#             testdetails = mongo.db.testDetails.find_one({"test_code":testCode})
#             user_details = mongo.db.users.find_one({"username":name})
#             user_test_report = mongo.db[f"{testCode}-result"].find_one({'name':name})
    
@main.route("/get_user_details",methods=['GET', 'POST'])
def get_user_details():
    """
    This function retrieves user details from a MongoDB collection based on the user ID stored in the
    session if the request method is POST.
    :return: The function `get_user_details` will return the user details if the request method is
    "POST" and the user is found in the MongoDB collection. If the request method is not "POST", it will
    return the string "METHOD NOT ALLOWED".
    """
    if request.method == "POST":
        user_id = session.get("user_id")
        user_details = mongo.db.users.find_one({'_id':ObjectId(user_id)},{'_id':0})
        return user_details
    return "METHOD NOT ALLOWED"

@main.route("/edit_details",methods=['GET', 'POST'])
def edit_details():
    """
    The `edit_details` function updates user details in a MongoDB database if the user is logged in,
    otherwise redirects to the login page.
    :return: The `edit_details` function returns either a rendered template for editing user details
    with the `studName` variable set to the current user's username if the user is logged in, or it
    redirects to the login page if the user is not logged in.
    """
    if check_login():
        if request.method == "POST":
            user_id = session.get("user_id")
            username,regno,Class,email,teacher = request.form["studName"],request.form["studRegno"],request.form["studClass"].upper(),request.form["studEmail"],request.form.get("teacherName")
            mongo.db.users.update_one({"_id":ObjectId(user_id)},{"$set":{"username":username,"regno":regno,"class":Class,"email":email,"teacher":teacher}})
        return render_template("edit_user_details.html",studName = session["username"])
    else:
        return redirect(url_for('main.login'))