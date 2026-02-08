from flask import Flask,jsonify,flash,session,Blueprint,request,redirect,url_for,render_template,json
from werkzeug.security import generate_password_hash,check_password_hash
from extensions import db
from models import User,PasswordReset
from sqlalchemy import or_
from datetime import timedelta,datetime
import secrets
from flask_mail import Message,Mail
import time
from collections import deque
from functools import wraps
import redis
import random

current_redis=redis.Redis(
    host="localhost",
    db=0,
    port=6379,
    decode_responses=True,
)


def generate_otp():
    return str(random.randint(100000,999999))

def check_login_ip(user_id,ip,k=3):
    key=f"login:{user_id}"
    current_redis.lpush(key,ip)
    current_redis.ltrim(key,0,k-1)
    current_redis.expire(key,300)
    ips=current_redis.lrange(key,0,-1)
    if len(ips)==k and len(set(ips))==k:
        return True
    return False

def block_user(user_id,minutes=10):
    current_redis.setex(f"blocked:{user_id}",minutes*60,user_id)
def is_user_blocked(user_id):
    return current_redis.exists(f"blocked:{user_id}")


 
REQUEST_LIMIT = 20
WINDOW_SIZE = 30

user_requests = {}  # user_id -> deque
def is_rate_limited(user_id):
    now = time.time()

    if user_id not in user_requests:
        user_requests[user_id] = deque()

    q = user_requests[user_id]

    # add current request
    q.append(now)

    # maintain fixed window size
    if len(q) > WINDOW_SIZE:
        q.popleft()

    # count requests in window
    if len(q) > REQUEST_LIMIT:
        return True

    return False

def rate_limit_middleware(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = request.form.get("id")

        if is_rate_limited(user_id):
            return jsonify({
                "error": "Rate limit exceeded"
            }), 429

        return fn(*args, **kwargs)
    return wrapper


v1_auth=Blueprint("v1_auth",__name__)
def generate_token():
    return secrets.token_urlsafe(32)

@v1_auth.route("/signin",methods=["POST"])
def signin_ui():
    if request.method=="POST":
        name=request.form.get("name")
        mobile=request.form.get("mobile")
        password=request.form.get("password")
        email=request.form.get("email")
        is_first_user=User.query.count()==0
        if len(name)<3:
            flash ("Name is minimum 5 alphabate")
            return redirect("/signin")
        if len(password)<4:
            flash("password is minimun 4 number")
            return redirect("/signin")
        if len(mobile)<10:
            flash("mobile number minimum 10 ")
            return redirect("/signin")
        hashed=generate_password_hash(password)
        user=User(name=name,email=email,password=hashed,mobile=mobile,role="admin" if is_first_user else "user")
        db.session.add(user)
        db.session.commit()
        print({"ip":request.remote_addr})
        flash("you are sign-in successfull")
        return render_template("login.html")
    return render_template("signin.html")

@v1_auth.route("/login", methods=["POST"])
@rate_limit_middleware
def login_ui():
    identifier = request.form.get("identifier")
    password = request.form.get("password")
    ip = request.remote_addr

    user = User.query.filter(
        or_(
            User.name == identifier,
            User.email == identifier,
            User.mobile == identifier
        )
    ).first()

    if not user:
        flash("user not found")
        return redirect("/login")
    
    if user and not check_password_hash(user.password,password):
        flash("incorrect password")
        return render_template("login.html")

    if is_user_blocked(user.id):
        flash("Account temporarily blocked")
        return redirect("/login")


    # ✅ Successful password
    if check_login_ip(user.id, ip):
        block_user(user.id)
        flash("Suspicious login detected. Account blocked for 10 minutes.")
        return redirect("/login")

    # ✅ FINAL SUCCESS
    print({"ip addresh":current_redis})
    session["user_id"] = user.id
    session["user_role"] = user.role
    flash("Login successful")
    return redirect("/addorder")


@v1_auth.route("/logout")
def logout_ui():
    if "user_id" not in session:
        flash("First login then logout")
        return redirect("/login")
    session.clear()
    flash("user logout successfull")
    return redirect("/login")

@v1_auth.route("/user/me")
def my_profile():
    if "user_id" not in session:
        return redirect("/login")
    user_id=session["user_id"]
    return jsonify({
        "id": user_id
    })
    
@v1_auth.route("/forget",methods=['POST'])
def forget_password():
    identifier=request.form.get("identifier")
    if not identifier:
        return jsonify("identifier is empty ")
    user=User.query.filter(or_(User.name==identifier,
                               User.email==identifier,
                               User.mobile==identifier)).first()
    if user:
        otp=generate_otp()
        redis_key=f"otp:{user.mobile}"
        current_redis.setex(redis_key,120,otp)
        session["reset_user_id"]=user.id
        print(f"otp :{otp} mobile : {user.mobile}")
        return render_template("check.html")
    flash("user not found")
    return render_template("forget.html")

@v1_auth.route("/checkotp",methods=["POST"])
@rate_limit_middleware
def check_otp():
    otp=request.form.get("otp")
    if not otp:
        return jsonify({"msg":"otp is required"})
    id=session["reset_user_id"]
    user=User.query.get(id)
    redis_key=f"otp:{user.mobile}"
    saved_otp=current_redis.get(redis_key)
    
    if saved_otp is None:
        return jsonify({"msg":"time limit is over key is expire"}),400
    if saved_otp==otp:
        flash("correct otp")
        return render_template("change_password.html")
    return jsonify({"msg":"incorrect otp"})
    
@v1_auth.route("/change-password",methods=["POST"])
@rate_limit_middleware
def change_password():
    if "reset_user_id" not in session:
        return render_template("forget.html")
    id=session["reset_user_id"]
    user=User.query.get(id)
    new_pass=request.form.get("new_password")
    new_pass_again=request.form.get("old_password")
    if new_pass != new_pass_again:
        flash("your both password not same")
        return render_template("change_password.html",user=user)
    user.password=generate_password_hash(new_pass)
    db.session.commit()
    flash("you shoping again order website")    
    return render_template("add_order.html")