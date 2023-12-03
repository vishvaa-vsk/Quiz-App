from flask_pymongo import PyMongo
mongo = PyMongo()
from flask import Flask

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://kvishvaa6:ownaVRLJiotzjVp5@cluster0.8lo1gvs.mongodb.net/QuizApp"
mongo = PyMongo(app)

@app.route("/")
def home_page():
    
    users = mongo.db.users.update_many({"class": {"$exists": True}},[{'$set': {'class': {'$toUpper': '$class'}}}])
    print(users)
    return "Hello"

if __name__ == "__main__":
    app.run()

