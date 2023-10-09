import jwt
import datetime
import os
from os import path
from dotenv import load_dotenv
from flask_mail import Message
from .extensions import mail
from flask import url_for,render_template


token_secret_key = os.environ.get("TOKEN_SECRET_KEY")

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(path.join(basedir,".env"))

def generate_token(userId,expires=600):
    reset_token = jwt.encode(
        {"payload":f"{userId}",
         "exp":datetime.datetime.now(tz=datetime.timezone.utc)+datetime.timedelta(seconds=expires)},
         token_secret_key,
         algorithm="HS256")
    return reset_token

def verify_token(token,userId):
    data = jwt.decode(token,token_secret_key,leeway=datetime.timedelta(seconds=20),algorithms=["HS256"])
    if data['payload'] == str(userId):
        return True
    if jwt.ExpiredSignatureError:
        return False
    
def send_email(token,userEmail,username):
    msg = Message('Password Reset Request For VEC Quiz App',sender='testvec26@gmail.com',recipients=[userEmail],)
    msg.body = f"""Hello {username},
      
A request has been received to change the password for your VEC Quiz app account.

Click this link to reset your password: {url_for('main.reset_password_verify',token=token,_external=True)}
      
If you did not initiate this request, please contact us immediately in communicative english lab!
      
Thank you,
The Communicative English Team
"""
    msg.html = render_template('reset_email_base.html',username=username,reset_token=token)
    mail.send(msg)

def send_email_admin(token,userEmail,username):
    msg = Message('Password Reset Request For VEC Quiz App',sender='testvec26@gmail.com',recipients=[userEmail],)
    msg.body = f"""Hello {username},
      
A request has been received to change the password for your VEC Quiz app account.

Click this link to reset your password: {url_for('admin.reset_admin_password_verify',token=token,_external=True)}
      
If you did not initiate this request, please contact us immediately in communicative english lab!
      
Thank you,
The Communicative English Team
"""
    msg.html = render_template('admin/reset_email_base.html',username=username,reset_token=token)
    mail.send(msg)

