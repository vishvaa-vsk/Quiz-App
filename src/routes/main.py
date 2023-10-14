from flask import Blueprint,flash,render_template,url_for,session,redirect,request,jsonify
from werkzeug.security import generate_password_hash,check_password_hash
from ..extensions import mongo,mail
from ..helper import generate_token,verify_token
from bson.objectid import ObjectId
from ..helper import send_email


main = Blueprint("main",__name__)

@main.route("/",methods=["GET","POST"])
def login():
    if request.method == "POST":
        session.permanent=True
        username,passwd = request.form["studName"],request.form["studPass"]
        if mongo.db.users.find_one({"username":username}):
            storedPasswd = mongo.db.users.find_one({"username":username})["passwd"]
            if check_password_hash(storedPasswd,passwd):
                session["username"] = username

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
        if not mongo.db.users.find_one({"username":username}):
            if passwd == repasswd:
                hashed_value = generate_password_hash(passwd,method='scrypt')
                try:
                    addUser = {"username":username,"class":Class,"regno":regno,"email":email,"passwd":hashed_value}
                    mongo.mongo.users.insert_one(addUser)
                    flash("Register Successfull")
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
    studName = session['username']
    return render_template('studentDashboard.html',studName=studName)

@main.route("/reset_request",methods=['GET', 'POST'])
def reset_request():
    if request.method == "POST":
        email = request.form['resetEmail']
        user = mongo.db.users.find_one({"email":email})
        forgot_users = mongo.db.forgot_users
        if user:
            token = generate_token(userId=str(user['_id']))
            send_email(userEmail=email,token=token,username=user['username'])
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
    return ""


@main.route("/test/<testCode>",methods=['GET', 'POST'])
def write_test(testCode):
    testDetails = list(mongo.db[testCode].find({},{"_id":0}))
    return render_template("showQuestions.html",testDetails=testDetails)