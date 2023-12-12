import requests
from requests.auth import HTTPDigestAuth
from ipify import get_ip

atlas_group_id = "653df42d84e83b2fb6e4b46b"

atlas_api_key_private = "6JIdZyLouXlnzWn6gMqug3LOrta3FPIST3PoRbvGbKWl03rDb1Ws9zX0jCxsUOp3"
ip = get_ip()

resp = requests.post(
    "https://cloud.mongodb.com/api/atlas/v1.0/groups/{atlas_group_id}/accessList".format(atlas_group_id=atlas_group_id),
    auth=HTTPDigestAuth(atlas_api_key_private),
    json=[{'ipAddress': ip, 'comment': 'From PythonAnywhere'}]  # the comment is optional
)
if resp.status_code in (200, 201):
    print("MongoDB Atlas accessList request successful", flush=True)
else:
    print(
        "MongoDB Atlas accessList request problem: status code was {status_code}, content was {content}".format(
            status_code=resp.status_code, content=resp.content
        ),
        flush=True
    )