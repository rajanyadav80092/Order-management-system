from flask import json,jsonify,redirect,render_template,request,flash,Blueprint,url_for
from models import User,Balance,Order
from extensions import db,jwt
from config import Config
from flask_jwt_extended import jwt_required,get_jwt_identity

v2_update=Blueprint("v2_update",__name__)

@v2_update.route("/update_user/<int:id>",methods=["POST","GET"])
@jwt_required(locations=["cookies"])
def update_user(id):
    identity=int(get_jwt_identity())
    current_user=identity
    if current_user != id:
        return redirect(url_for("v2_update.update_user",id=current_user))
    up_user=User.query.get(id)
    if request.method!="POST":
        return render_template("update_user.html",user=up_user)
    up_user.name=request.form.get("name")
    up_user.email=request.form.get("email")
    up_user.password=request.form.get("password")
    up_user.mobile=request.form.get("mobile")
    
    db.session.commit()
    return jsonify({"msg":"your are updated successfully"})
    

@v2_update.route("/update_balance/<int:id>",methods=["POST","GET"])
@jwt_required(locations=["cookies"])
def update_balance(id):
    identity=int(get_jwt_identity())
    current_id=identity
    if current_id != id:
        return redirect(url_for("v2_orders.update_balance",id=current_id))
    up_bal=Balance.query.filter_by(user_bal=id).first()
    if request.method!="POST":
        return render_template("update_balance.html",balance=up_bal)
    up_bal.account_num=request.form.get("account_num")
    up_bal.name=request.form.get("name")
    up_bal.password=request.form.get("password")
    
    db.session.commit()
    flash("your bank account update successfull")
    return redirect("/addorder")

    
    
    
        
        