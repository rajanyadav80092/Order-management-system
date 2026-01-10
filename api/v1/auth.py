from flask import Flask,jsonify,flash,session,Blueprint,request,redirect,url_for,render_template
from werkzeug.security import generate_password_hash,check_password_hash
from extensions import db
from models import User,PasswordReset
from sqlalchemy import or_
from datetime import timedelta,datetime
import secrets
from flask_mail import Message,Mail
from config import Config




v1_auth=Blueprint("v1_auth",__name__)
def generate_token():
    return secrets.token_urlsafe(32)

@v1_auth.route("/signin",methods=["POST","GET"])
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
        flash("you are sign-in successfull")
        return redirect("/login")
    return redirect("signin.html")

@v1_auth.route("/login",methods=["POST","GET"])
def login_ui():
    if request.method=="POST":
        identifier=request.form.get("identifier")
        password=request.form.get("password")
        
        user=User.query.filter(or_(
            identifier==User.name,
            identifier==User.email,
            identifier==User.mobile
        )).first()
        
        if not user:
            flash("user is not found")
            return redirect("/login")
        if user and check_password_hash(user.password,password):
            session["user_id"]=user.id
            session["user_role"]=user.role
            flash("user login successfull")
            return redirect("/addorder")
        flash("please check your password")
        return redirect("/login")
    return redirect("/login")

@v1_auth.route("/logout")
def logout_ui():
    if "user_id" not in session:
        flash("First login then logout")
        return redirect("/login")
    session.clear()
    db.session.commit()
    flash("user logout successfull")
    return redirect("/login")

@v1_auth.route("/forget-password",methods=["POST","GET"])
def forget_password():
    if request.method=="GET":
        return render_template("forget.html")  
    email=request.form.get("email")
    user=User.query.filter_by(email=email).first()
    if not user:
        flash("email id not found please put correct email")
        return render_template("forget.html")
    flash("put new password")
    return render_template("change_password.html",user=user)
    
@v1_auth.route("/change-password/<int:id>",methods=["POST"])
def change_password(id):
    user=User.query.filter_by(id=id).first()
    new_pass=request.form.get("new_password")
    new_pass_again=request.form.get("old_password")
    if new_pass != new_pass_again:
        flash("your both password not same")
        return render_template("change_password.html",user=user)
    user.password=generate_password_hash(new_pass)
    db.session.commit()
    flash("your password change successfull")    
    return redirect("/login")
        
