from flask import Flask, render_template, request, session, redirect, url_for
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import jsonify, send_from_directory
from bson.objectid import ObjectId
import os
from datetime import datetime
from time import time

UPLOAD_FOLDER = '/home/mrahul16/Documents/PESU/CCBD/Assignments/photoshare/uploads'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "photosharerandomsecretkey"
client = MongoClient()
client = MongoClient('localhost', 27017)

db = client.photosharedb

users = db.users
photos = db.photos
frequests = db.friend_requests


@app.context_processor
def frequests_processor():
    if is_authenticated():
        from_people = frequests.find({"to": session["_id"]}, {"from": 1, "_id": 0})
        if from_people is None:
            return render_template('index.html', fr={"norequests": True})
        from_ids = list(map(lambda x: x["from"], from_people))
        fr = list(users.find({"_id": {"$in": from_ids}}, {"firstname": 1, "lastname": 1}))
        return {"fr": fr}
    return {"fr": []}


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route("/")
def index():
    if is_authenticated():
        friends = users.find_one({"_id": session["_id"]}, {"friends": 1, "_id": 0})
        if friends["friends"] != []:
            photolist = list(photos.find({"user": {"$in": friends["friends"]}}))
            for photo in photolist:
                if session["_id"] in photo["likes"]:
                    photo["liked"] = 1
                else:
                    photo["liked"] = 0
                photo["likeCount"] = len(photo["likes"])
            return render_template('index.html', photos=photolist)
        return render_template('index.html', photos=[])
    return render_template('login.html')


@app.route("/user/profile")
def profile():
    if is_authenticated():
        # if photos.user == session.user:
        # print(photos.user)
        # print(session)
        photolist = list(photos.find({"user": session["_id"]}))
        print(photolist)
        # image_names = os.listdir('./uploads')
        return render_template('profile.html', photos=photolist, count=len(photolist))
    return render_template('login.html')


@app.route("/user/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        loginform = request.form
        user = users.find_one({"email": loginform["email"]})
        if user is None:
            return redirect(url_for('index'))
        if check_password_hash(user["password"], loginform["password"]):
            set_session(user["firstname"], user["lastname"], user["_id"])
            return redirect(url_for('index'))
    return redirect(url_for('index'))

@app.route("/user/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        signupform = request.form
        user = {
            "firstname": signupform["firstname"],
            "lastname": signupform["lastname"],
            "_id": strip_email(signupform["email"]),
            "email": signupform["email"],
            "password": generate_password_hash(signupform["password"]),
            "friends": []
        }
        try:
            users.insert_one(user)
        except Exception as e:
            return redirect(url_for('login'))
        set_session(user["firstname"], user["lastname"], user["_id"])
        return redirect(url_for('index'))
    return redirect(url_for('login'))


@app.route("/user/logout", methods=['GET', 'POST'])
def logout():
    clear_session()
    return redirect(url_for('index'))


@app.route('/user/addphoto', methods=['GET', 'POST'])
def addphoto():
    filename = ""
    if is_authenticated():
        if request.method == 'POST':
            # check if the post request has the file part
            if 'file' not in request.files:
                return redirect(request.url)
            fileform = request.form
            file = request.files['file']
            # if user does not select file, browser also
            # submit a empty part without filename
            if file.filename == '':
                print("A file has no name")
                return redirect(request.url)
            if file:
                filename = file.filename[::-1]
                print(filename)
                filename = (filename[: filename.index('.')])[::-1]
                filename = session["_id"] + str(time()) + "." + filename
                filename = secure_filename(filename)
                fileobj = {
                    "name": fileform["name"],
                    "description": fileform["description"],
                    "added": datetime.now(),
                    "likes": [],
                    "user": session["_id"],
                    "file": filename,
                    "username": session["firstname"] + " " + session["lastname"]
                }
                photos.insert_one(fileobj)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                return redirect(request.url)
    return redirect(url_for('index'))


@app.route('/user/addfriend', methods=['GET', 'POST'])
def addfriend():
    email = ""
    if is_authenticated():
        if request.method == 'POST':
            addfriendform = request.form
            email = addfriendform["email"]
            person = users.find_one({"email": email})
            if person is None:
                print("Oops")
                session["error"] = email + " does not belong to a registered user"
                return redirect(request.url)
            frequest = {
                "from": session["_id"],
                "to": person["_id"]
            }
            frequests.insert_one(frequest)
            return redirect(request.url)
    return redirect(url_for('index'))


@app.route('/user/acceptrequest/<fromperson>/<toperson>', methods=['GET', 'POST'])
def acceptrequest(fromperson, toperson):
    if is_authenticated():
        # if request.method == 'POST':
        frequest = frequests.find_one({"from": fromperson, "to": toperson})
        if frequest is None:
            return jsonify({"success": 0})
        two_people = users.find({"_id": {"$in": [frequest["from"], frequest["to"]]}})
        first = two_people[0]
        second = two_people[1]
        first["friends"].append(second["_id"])
        second["friends"].append(first["_id"])
        print(first["friends"])
        print(second["friends"])
        users.update({"_id": first["_id"]}, {"$set": {"friends": first["friends"]}})
        users.update({"_id": second["_id"]}, {"$set": {"friends": second["friends"]}})
        frequests.remove({"_id": frequest["_id"]})
        return jsonify({"success": 1})
    return redirect(url_for('index'))


@app.route('/user/like', methods=['GET', 'POST'])
def like():
    if is_authenticated():
        if request.method == 'POST':
            photodata = request.json
            print(photodata)
            photo = photos.find_one({"_id": ObjectId(photodata["id"])})
            print(photo)
            photo["likes"].append(photodata["user"])
            photos.update({"_id": ObjectId(photodata["id"])}, {"$set": {"likes": photo["likes"]}})
            return jsonify({"success": 1})
        return redirect(request.url)
    return redirect(url_for('index'))


def set_session(firstname, lastname, email):
    session["firstname"] = firstname
    session["lastname"] = lastname
    session["_id"] = email
    session["error"] = ""
    # db.friend_requests.aggregate([{$lookup:{from:"users",localField:"to",foreignField:"_id",as:"requestsList"}},{$match: { "from": "tyrionlannistercom" }}])



def clear_session():
    if is_authenticated():
        session.pop('firstname', None)
        session.pop('lastname', None)
        session.pop('_id', None)


def is_authenticated():
    return '_id' in session


def strip_email(email):
    return (email.replace("@", "")).replace(".", "")


if __name__ == "__main__":
    app.run(debug=True)
