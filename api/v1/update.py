from flask import Flask,redirect,flash,Blueprint,session,url_for,request,render_template
from models import User,Balance
from extensions import db
from config import Config
from werkzeug.security import generate_password_hash,check_password_hash

v1_update=Blueprint("v1_update",__name__)

@v1_update.route("/update_bank/<int:id>",methods=["POST","GET"])
def update_bank(id):
    if "user_id" not in session:
        return redirect("/login")
    if session["user_id"] != id:
        return redirect(url_for("v1_update.update_bank",id=session["user_id"]))
    
    balance=Balance.query.filter_by(user_bal=id).first()
    if not balance:
        flash("balance id not found")
        return redirect(url_for("v1_orders.add_balance"))
    
    if request.method=="POST":
        balance.name=request.form.get("name")
        balance.password=request.form.get("password")
        balance.account_num=request.form.get("account_num")
        
        db.session.commit()
        flash("bank account update successfull")
        return redirect("/addorder")
    return render_template("update_balance.html",balance=balance)

@v1_update.route("/update_user/<int:id>",methods=["POST","GET"])
def update_user(id):
    if "user_id" not in session:
        return redirect("/login")
    if session["user_id"] != id:
        return redirect(url_for("v1_update.update_user",id=session["user_id"]))
    user=User.query.get(id)
    if request.method=="POST":
        user.name=request.form.get("name")
        user.email=request.form.get("email")
        user.mobile=request.form.get("mobile")
        user.password=generate_password_hash(request.form.get("password"))
        db.session.commit()
        flash("user update successfully")
        return redirect("/addorder")
    return render_template("update_user.html",user=user)

