import pandas as pd
import os
import json

execel_file_path = os.path.abspath("demo.xlsx")

df = pd.read_excel(execel_file_path,engine='openpyxl')

questions_json = df.to_json(orient='records')


thisisjson_dict = json.loads(questions_json)

questions_list = []

for i in thisisjson_dict:
    del i["Unnamed: 2"]
    del i["Unnamed: 3"]
    questions_list.append(i)

print(questions_list)