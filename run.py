from operator import truediv
from flask import Flask
from flask import request
from flask import render_template
from flask_pymongo import PyMongo
from datetime import datetime
from datetime import timedelta
from bson.objectid import ObjectId
from flask import abort
from flask import redirect
from flask import url_for
from flask import flash
from flask import session
from functools import wraps
import random
import time
import math
import os

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/software_web"
app.secret_key = os.urandom(24)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes = 30) #30분이 지나면 자동 로그아웃
mongo = PyMongo(app)
    
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("id") is None or session.get("id") == "":
            return redirect(url_for("member_login", next_url=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.template_filter("formatdatetime")
def format_datetime(value):
    if value is None:
        return ""
    
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    value = datetime.fromtimestamp(int(value) / 1000) + offset
    return value.strftime('%Y.%m.%d. %H:%M')

@app.route("/mywrite")
@login_required
def lists_mywrite():
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", 10, type=int)
    search = request.args.get("search", -1, type=int)
    keyword = request.args.get("keyword", "",  type=str)
    query = {}
    search_list = []
    
    search_list.append({"name": {"$regex": keyword}})
    if len(search_list) > 0:
        query = {"$or": search_list}
    print(query)
    board = mongo.db.board
    datas = board.find(query).skip((page - 1)*limit).limit(limit).sort("pubdate", -1)
    tot_count = board.count_documents(query)
    last_page_num = math.ceil(tot_count / limit)
    block_size = 5
    block_num = int((page - 1) / block_size)
    block_start = int((block_size*block_num) + 1)
    block_last = math.ceil(block_start + (block_size - 1))
    return render_template("mywrite.html", datas=list(datas), limit=limit, page=page, block_start=block_start, block_last=block_last, last_page_num=last_page_num, search=search, keyword=keyword)

@app.route("/mypage")
@login_required
def lists_mypage():
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", 10, type=int)
    search = request.args.get("search", -1, type=int)
    keyword = request.args.get("keyword", "",  type=str)
    query = {}
    search_list = []
    
    search_list.append({"name": {"$regex": keyword}})
    if len(search_list) > 0:
        query = {"$or": search_list}
    print(query)
    board = mongo.db.board
    datas = board.find(query).skip((page - 1)*limit).limit(limit).sort("pubdate", -1)
    tot_count = board.count_documents(query)
    last_page_num = math.ceil(tot_count / limit)
    block_size = 5
    block_num = int((page - 1) / block_size)
    block_start = int((block_size*block_num) + 1)
    block_last = math.ceil(block_start + (block_size - 1))
    return render_template("mypage.html", datas=list(datas), limit=limit, page=page, block_start=block_start, block_last=block_last, last_page_num=last_page_num, search=search, keyword=keyword)

@app.route("/list")
def lists():
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", 10, type=int)
    search = request.args.get("search", -1, type=int)
    keyword = request.args.get("keyword", "",  type=str)
    query = {}
    search_list = []
    
    if search == 0:
        search_list.append({"title": {"$regex": keyword}})
    if len(search_list) > 0:
        query = {"$or": search_list}
    print(query)
    board = mongo.db.board
    datas = board.find(query).skip((page - 1)*limit).limit(limit).sort("pubdate", -1)
    tot_count = board.count_documents(query)
    last_page_num = math.ceil(tot_count / limit)
    block_size = 5
    block_num = int((page - 1) / block_size)
    block_start = int((block_size*block_num) + 1)
    block_last = math.ceil(block_start + (block_size - 1))
    return render_template("list.html", datas=list(datas), limit=limit, page=page, block_start=block_start, block_last=block_last, last_page_num=last_page_num, search=search, keyword=keyword)



@app.route("/view/<idx>")
def board_view(idx):
    if idx is not None:
        page = request.args.get("page")
        search = request.args.get("search")
        keyword = request.args.get("keyword")
        
        board = mongo.db.board
        data = board.find_one({"_id": ObjectId(idx)})
        
        if data is not None:
            result = {
                "id": data.get("_id"),
                "name": data.get("name"),
                "title": data.get("title"),
                "writer_id": data.get("writer_id", ""),
                "contents": data.get("contents"),
                "onsaledisplay": data.get("onsaledisplay"),
                "pubdate": data.get("pubdate"),
            }
            
            return render_template("view.html", result = result, page=page, search=search, keyword=keyword)
        return abort(400)
        

@app.route("/write", methods = ["GET", "POST"])
@login_required
def board_write(): 
    if request.method == "POST":
        name = request.form.get("name")
        title = request.form.get("title")
        contents = request.form.get("contents")
        onsaledisplay = request.form.get("onsaledisplay")
        
        current_utc_time = round(datetime.utcnow().timestamp() * 1000)
        board = mongo.db.board
        post = {
            "name": name,
            "title": title,
            "writer_id": session.get("id2"),
            "contents": contents,
            "onsaledisplay": onsaledisplay,
            "pubdate":current_utc_time,
        }
        
        x = board.insert_one(post)
        return redirect(url_for("board_view", idx = x.inserted_id))
    else:
        return render_template("write.html")
    
# @app.route("/follow", methods = ["GET", "POST"])
# @login_required
# def user_follow(): 
#     if request.method == "POST":
#         dest = request.form.get("dest")
#         follower = request.form.get("follower")
        
#         followboard = mongo.db.followboard
#         post = {
#             "dest": dest,
#             "follower": follower,
#         }
        
#         x = followboard.insert_one(post)
#         return 
#     else:
#         return render_template("view.html")

@app.route("/join", methods=["GET", "POST"])
def member_join():
    if request.method == "POST":
        id = request.form.get("id", type=str)
        pass1 = request.form.get("pass1", type=str)
        pass2 = request.form.get("pass2", type=str)
        name = request.form.get("name", type=str)
        
        if id == "" or pass1 == "" or pass2 == "" or name == "":
            flash("입력되지 않은 값이 있습니다.")
            return render_template("join.html")
        
        if pass1 != pass2:
            flash("비밀번호가 일치하지 않습니다.")
            return render_template("join.html")
        
        members = mongo.db.members
        cnt = members.count_documents({"id": id})
        if cnt > 0:
            flash("중복된 아이디 입니다.")
            return render_template("join.html")
        
        current_utc_time = round(datetime.utcnow().timestamp()*1000)
        post = {
            "id": id,
            "pass1": pass1,
            "pass2": pass2,
            "name": name,
            "joindate": current_utc_time,
            "logintime": "",
            "logincount": 0,
        }
        
        members.insert_one(post)
        
        return render_template("login.html")
    else:
        return render_template("join.html")
    
@app.route("/login", methods=["GET", "POST"])
def member_login():
    if request.method == "POST":
        id = request.form.get("id")
        password = request.form.get("pass1")
        
        members = mongo.db.members
        data = members.find_one({"id": id})
        
        if data is None:
            flash("회원 정보가 없습니다.")
            return redirect(url_for("member_login"))
        else:
            if data.get("pass1") == password:
                session["id"] = id
                session["name"] = data.get("name")
                session["id2"] = str(data.get("_id"))
                session.permanent = True
                return redirect(url_for("lists"))
            else:
                flash("비밀번호가 일치하지 않습니다.")
                return redirect(url_for("member_login"))
        
        return ""
    else:
        return render_template("login.html")
    
@app.route("/edit/<idx>", methods=["GET", "POST"])
def board_edit(idx):
    if request.method == "GET":
        board = mongo.db.board
        data = board.find_one({"_id": ObjectId(idx)})
        if data is None:
            flash("해당 게시물이 존재하지 않습니다.")
            return redirect(url_for("lists"))
        else:
            if session.get("id2") == data.get("writer_id"):
                return render_template("edit.html", data=data)
            else:
                flash("글 수정 권한이 없습니다.")
                return redirect(url_for("lists"))
    else:
        title = request.form.get("title")
        contents = request.form.get("contents")
        onsaledisplay = request.form.get("onsaledisplay")
        
        board = mongo.db.board
        data = board.find_one({"_id": ObjectId(idx)})
        if session.get("id2") == data.get("writer_id"):
            board.update_one({"_id":ObjectId(idx)}, {
                "$set": {
                    "title": title,
                    "contents": contents,
                    "onsaledisplay": onsaledisplay
                }
            })
            flash("수정되었습니다.")
            return redirect(url_for("board_view", idx=idx))
        else:
            flash("글 수정 권한이 없습니다.")
            return redirect(url_for("lists"))
        
        
    return ""

@app.route("/delete/<idx>")
def board_delete(idx):
    board = mongo.db.board
    data = board.find_one({"_id": ObjectId(idx)})
    if session.get("id2") == data.get("writer_id"):
        board.delete_one({"_id": ObjectId(idx)})
        flash("삭제 되었습니다.")
    else:
        flash("삭제 권한이 없습니다.")
    return redirect(url_for("lists"))

@app.route("/logout")
def member_logout():
    try:
        del session["name"]
        del session["id2"]
        del session["id"]
    except:
        pass
    return redirect(url_for('lists'))
    

if __name__ == "__main__":
    app.run(debug=True, port = 9000)
