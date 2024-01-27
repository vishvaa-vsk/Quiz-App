from collections import defaultdict
from pprint import pprint

l = [{'_id': '658bc00c279b1b817835d211',
  'class': 'I-CSE-B',
  'name': 'Vishvaa K',
  'percentage': 100.0,
  'regno': '113223031238',
  'score': 100.0,
  'status': 'Pass',
  'teacher': 'Balaji A',
  'test_code': 'HSJQZPBX'},
 {'_id': '65b4f76ee1bddb3d64c8221a',
  'class': 'I-CSE-B',
  'name': 'Vishvaa K',
  'percentage': 100,
  'regno': '113223031238',
  'score': 100,
  'status': 'Pass',
  'teacher': 'Vinothkumar M',
  'test_code': '7S05G1K6',
  'test_type': 'University Exam'},
 {'_id': '658bc00c279b1b817835d211',
  'class': 'I-CSE-B',
  'name': 'Vishvaa K',
  'percentage': 100.0,
  'regno': '113223031238',
  'score': 100.0,
  'status': 'Pass',
  'teacher': 'Vinothkumar M',
  'test_code': 'XZYDEMO123'},
 {'_id': '658bc00c279b1b817835d211',
  'class': 'I-CSE-B',
  'name': 'Vishvaa K',
  'percentage': 100.0,
  'regno': '113223031238',
  'score': 100.0,
  'status': 'Fail',
  'teacher': 'Vinothkumar M',
  'test_code': '07ZVBML8',
  'test_type': 'University Exam'}]

grouped_data = defaultdict(list)

for item in l:
    key = (item['name'], item['regno'], item['class'])
    score = item['score']
    test_code = item['test_code']
    grouped_data[key].append({'score': score, 'test_code': test_code})

grouped_list = [{'name': name, 'regno': regno, 'class': class_, 'scores': data} 
                for (name, regno, class_), data in grouped_data.items()]


print(grouped_list)
# marks = 0
# for i in range(len(grouped_list)):
#     print(f"S.NO {i+1}")
#     print(grouped_list[i]["regno"])
#     print(grouped_list[i]["name"])
#     for scores in grouped_list[i]["scores"]:
#         print(scores["test_code"],scores["score"])
#         marks+=scores["score"]
# print(f"{marks/10}/40")
    