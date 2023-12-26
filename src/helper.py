import jwt
from datetime import datetime,date,timezone,timedelta
import os
from os import path
from dotenv import load_dotenv
from flask import render_template
import pandas as pd
import json

token_secret_key = os.environ.get("TOKEN_SECRET_KEY")

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(path.join(basedir,".env"))

def generate_token(userId,expires=600):
    reset_token = jwt.encode(
        {"payload":f"{userId}",
         "exp":datetime.now(tz=timezone.utc)+timedelta(seconds=expires)},
         token_secret_key,
         algorithm="HS256")
    return reset_token

def verify_token(token,userId):
    data = jwt.decode(token,token_secret_key,leeway=timedelta(seconds=20),algorithms=["HS256"])
    if data['payload'] == str(userId):
        return True
    if jwt.ExpiredSignatureError:
        return False

def create_report(name,class_and_sec,testCode,regno,status,score,percentage,lab_session,audio_no,file):
    today = date.today()
    now = datetime.now()
    todays_date = today.strftime("%d %B %Y")
    todays_time = now.strftime("%H:%M %p")
    template = render_template(f"{file}",name=name,Class=class_and_sec,TestCode=testCode,regno=regno,status=status,score=score,percentage=percentage,time=todays_time,Date=todays_date,lab_session=lab_session,audio_no=audio_no)
    return template


def create_csv(filename,report_details):
    import csv
    fields = ['name','score','percentage','status']
    with open(os.path.join(os.path.abspath("Quiz-App/admin_reports"),filename),"w+") as csvfile:
        writer = csv.DictWriter(csvfile,fieldnames=fields)
        writer.writeheader()
        writer.writerows(report_details)

def extract_questions(filepath):
    file_content = pd.read_excel(filepath,engine='openpyxl')
    json_object = file_content.to_json(orient='records')
    raw_dict = json.loads(json_object)
    questions_list = []
    for i in raw_dict:
        list_keys = list(i.keys())
        for j in list_keys:
            if j.startswith("Unnamed"):
                i.pop(j)
        questions_list.append(i)
    return questions_list
