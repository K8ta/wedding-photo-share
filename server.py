# -*- coding: utf-8 -*-

import os
from flask import Flask, render_template, request, flash, redirect, url_for, session, make_response, send_from_directory
from flask_pymongo import PyMongo
import pymongo
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import json
import datetime
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
import random
from datetime import datetime
import uuid
import requests

app = Flask(__name__)
app.secret_key = 'secret'

app.config["MONGO_URI"] = ["MONGO_URI"]
mongo = PyMongo(app)

gauth = GoogleAuth()
gauth.CommandLineAuth()
drive = GoogleDrive(gauth)

# アップロードされる拡張子の制限
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'gif'])

users = mongo.db.users.find()
users = {str(v["_id"]): v["name"] for v in users}
ranking_flg="0"

@app.before_request
def before_request():
    # https通信にするおまじない 
    if not request.headers.get('X-Forwarded-Proto', 'http') == 'https':
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)
    # セッション切れた時の処理
    if(session.get("userid") == None and request.method == "GET"):
        if(request.path == "/gallery" or request.path == "/ranking" or request.path == "/admin" or request.path == "/ajax"):
            return redirect('/')
        else:
            return
    else:
        return

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/img'), 'favicon.ico')

@app.route('/apple-touch-icon.png')
def apple_touch_icon():
    return send_from_directory(os.path.join(app.root_path, 'static/img'), 'apple-touch-icon.png')

@app.route('/apple-touch-icon-precomposed.png')
def apple_touch_icon_precomposed():
    return send_from_directory(os.path.join(app.root_path, 'static/img'), 'apple-touch-icon-precomposed.png')

@app.route("/", methods=['GET'])
def index():
    userid = request.args.get('userid', '')
    if userid != "":
        try:
            if userid in [k for k, v in users.items()]:
                session['userid'] = userid
            else:
                return "QRコードを再度読み込んでください。"
        except:
            return "QRコードを再度読み込んでください。"
    else:
        userid = session.get("userid")
        if userid == None:
            return "QRコードを再度読み込んでください。"
    return redirect("/gallery")


@app.route("/gallery", methods=['GET', 'POST'])
def gallery():
    return render_template("gallery_smart.html", title="gallery")

@app.route('/ajax', methods=['GET','POST'])
def ajax():
    if(ranking_flg == "1"):
        return ""
    else:
        userid = session.get("userid")
        photo = mongo.db.photo.find().sort([("time",pymongo.DESCENDING)])
        return render_template("ajax.html", title="gallery", photo=photo, userid=userid, mode=ranking_flg)


@app.route('/like', methods=['POST'])
def test():
    userid = session.get("userid")
    res = request.form['like']
    mongo.db.photo.update_one({"_id": ObjectId(res)}, {
                              "$push": {"likeusers": userid}})
    flash('New entry was successfully posted')
    return redirect("/gallery")


@app.route('/upload', methods=['POST'])
def upload_multipart():
    # ファイルがなかった場合の処理
    if 'file' not in request.files:
        flash('ファイルがありません')
        return redirect("/gallery")
    # データの取り出し
    file = request.files['file']
    # ファイル名がなかった時の処理
    if file.filename == '':
        flash('ファイルがありません')
        return redirect("/gallery")
    if file:
        try:
            filename = str(uuid.uuid4()) + ".jpg"
            file.save(os.path.join("./", filename))
            folder_id = [フォルダID]
            f = drive.CreateFile({'title': '1.jpg',
                                  'mimeType': 'image/jpeg',
                                  'parents': [{'kind': 'drive#fileLink', 'id': folder_id}]})
            f.SetContentFile(filename)
            flash('New entry was successfully posted')
            f.Upload()
            image_url = str(f['thumbnailLink']).split("=")[0]+"=s740"
            mongo.db.photo.insert_one({"photid": image_url, "likeusers": [
            ], "userid": session["userid"], "time": datetime.now().strftime('%Y%m%d%H%M%S%f')})
            f.clear()
            file.close()
            del file
            del f
            os.remove(filename)
        except:
            return redirect("/gallery") 
    return url_for('gallery',
        _external=True,
        _scheme='https',
        )


@app.route("/ranking", methods=['GET'])
def ranking():
    # すてき数の多い上位3件の取得
    ranking = mongo.db.photo.aggregate([{"$unwind": "$likeusers"},
                                        {"$group": {"_id": "$_id", "userid": {"$first": "$userid"}, "photid": {
                                            "$first": "$photid"}, "size": {"$sum": 1}}},
                                        {"$sort": {"size": -1, "_id": -1}},
                                        {"$group": {"_id": "$userid", "score": {
                                            "$first": "$size"}, "photid": {"$first": "$photid"}}},
                                        {"$sort": {"score": -1, "_id":1}},
                                        {"$limit": 3}
                                        ])
    print(ranking)
    prize = ["最優秀賞", "準優秀賞", "佳作"]
    no = [1,2,3]
    return render_template("ranking.html", title="ranking", ranking=zip(no,ranking, prize), users=users)


@app.route("/admin", methods=['POST',"GET"])
def admin():
    if(request.method == "POST"):
        global ranking_flg 
        ranking_flg = request.form['mode']
        return render_template("admin.html", title="admin", ranking_flg=ranking_flg)
    else:
        return render_template("admin.html", title="admin", ranking_flg=ranking_flg)


# Heroku用の設定
if __name__ == '__main__':
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
