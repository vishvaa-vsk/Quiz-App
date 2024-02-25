import jwt
from datetime import datetime,date,timezone,timedelta
import os
from os import path
from dotenv import load_dotenv
from flask import render_template
import pandas as pd
import json
import pytz
from .extensions import mongo

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
    indiaTz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(indiaTz)
    todays_date = today.strftime("%d %B %Y")
    todays_time = now.strftime("%H:%M %p")
    template = render_template(f"{file}",name=name,Class=class_and_sec,TestCode=testCode,regno=regno,status=status,score=score,percentage=percentage,time=todays_time,Date=todays_date,lab_session=lab_session,audio_no=audio_no)
    return template


def remove_duplicates(iterable):
    copy = set(iterable)
    non_duplicate = list(copy)
    return non_duplicate

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

def clean_reports(test_codes,dept,regex):
    from collections import defaultdict
    uncleaned_reports = []
    for test in test_codes:
        if dept == "CSE(CS)":
            documents = mongo.db[test].find({"class":"I-CSE(CS)-A"})
        else:
            documents = mongo.db[test].find({"class":{"$regex":regex}})
        for result in documents:
            uncleaned_reports.append(result)
    grouped_data = defaultdict(list)
    for item in uncleaned_reports:
        key = (item['name'], item['regno'])
        score = item['score']
        test_code = item['test_code']
        grouped_data[key].append({'score': score, 'test_code': test_code})

    cleaned_reports = [{'name': name, 'regno': regno,'scores': data} for (name, regno), data in grouped_data.items()]

    cleaned_reports_sorted = sorted(cleaned_reports, key=lambda x: x['regno'])
    return cleaned_reports_sorted