from flask import render_template,redirect,request,url_for,flash,Blueprint,jsonify,json
from models import User,Balance,Order
from extensions import jwt,db
from config import Config
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import get_jwt_identity,jwt_required,get_jwt
import redis
import time
from functools import wraps

v2_orders=Blueprint("v2_orders",__name__)

current_redis=redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

def admin_required(fn):
    @wraps(fn)
    @jwt_required(locations=["cookies"])
    def wrapper(*args, **kwargs):
        claims = get_jwt()

        if claims.get("role") != "admin":
            flash("admin axis required ")
            return redirect("/login")

        return fn(*args, **kwargs)
    return wrapper

def user_required(fn):
    @wraps(fn)
    @jwt_required(locations=["cookies"])
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper

    
@v2_orders.route("/balance-add",methods=["POST","GET"])
@user_required
def balance_add():
    current_user_id=int(get_jwt_identity())
    if request.method=="POST":
        account_num=request.form.get("account_num")
        account_name=request.form.get("name")
        balan=request.form.get("balance")
        password=request.form.get("password")
        
        bal=Balance(account_num=account_num,account_name=account_name,balance=balan,password=password,user_bal=current_user_id)
        db.session.add(bal)
        db.session.commit()
        flash("balance added successfully")
        return redirect("/addorder")
    return render_template("balance.html")

@v2_orders.route("/add-balance",methods=["POST","GET"])
@user_required
def add4_balance():
    current_user_id=int(get_jwt_identity())
    bal=Balance.query.filter_by(user_bal=current_user_id).first()
    if not bal:
        flash("balance id is not found create your account")
        return redirect(url_for("v2_orders.balance_add"))
    if request.method=="POST":
        password=request.form.get("password")
        if bal.password != password:
            flash("please put your old password")
            return redirect(url_for("v2_orders.add4_balance"))
        try:
            amount=int(request.form.get("amount"))
            bal.balance+=amount
            db.session.add(bal)
            db.session.commit()
            flash("amount added successfull")
            return redirect(url_for("v2_orders.add_order"))
        except (TypeError,ValueError):
            db.session.rollback()
            flash("Invalid Amount")
            return redirect(url_for("v2_orders.add4_balance"))
    return render_template("add_balance.html",bal=bal)
        

@v2_orders.route("/add-order",methods=["POST","GET"])
@user_required
def add_order():
    current_user_id=int(get_jwt_identity())
    if request.method=="POST":
        product=request.form.get("product")
        bal=Balance.query.filter_by(user_bal=current_user_id).first()
        if not bal:
            flash("balance id not found")
            return redirect(url_for("v2_orders.add4_balance"))
            
        try:
            amount=int(request.form.get("amount"))
        except (TypeError, ValueError):
            flash("Invalid amount")
            return redirect(url_for("v2_orders.add_order"))
        
        if bal.balance<amount:
            flash("your  balance less  then order amount ")
            return redirect(url_for("v2_orders.add4_balance"))
        try:
            bal.balance-=amount
            order=Order(amount=amount,product=product,user_id=current_user_id)
            db.session.add(order)
            db.session.add(bal)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error":"user order is not added"})
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "error": "transaction failed",
                "message": str(e)
            })
        flash("your order added successfully")
        return redirect(url_for("v2_orders.add_order"))
    return render_template("add_order.html")
        
@v2_orders.route("/order/<int:id>/user")
def order_user(id):
    order=Order.query.get(id)
    if not order:
        return jsonify({"error":"your order id not found"})
    return jsonify({
        "product":order.product,
        "order":order.id,
        "amount":order.amount,
        "user_id":order.user_id,
        "user_name":order.user.name
    })
    
@v2_orders.route("/user/<int:id>/order")
def user_order(id):
    current_user_id=int(get_jwt_identity())
    if current_user_id != id:
        return redirect(url_for("v2_orders.user_order",id=current_user_id))
    row=[]
    user=User.query.get(id)
    for o in user.orders:
        row.append({
            "product":o.product,
            "amount":o.amount,
            "order_id":o.id,
        })
    return jsonify({
        "user":row,
        "user_name":user.name,
        "user_id":o.user_id
    })
    
@v2_orders.route("/balance/<int:id>")
def user_balance(id):
    current_user_id=int(get_jwt_identity())
    if current_user_id != id:
        return redirect(url_for("v2_orders.user_balance",id=int(current_user_id)))
    balanc=Balance.query.filter_by(user_bal=id).first()
    if  not balanc:
        flash("first add balance")
        return redirect(url_for("v2_orders.balance_add"))
    return jsonify({
        "balance":balanc.balance,
        "account_holder_name":balanc.account_name,
        "account_num":balanc.account_num,
        "id":balanc.id,
        "user_id":balanc.user_bal,
        "user_name":balanc.user.name
    })
          
        
@v2_orders.route("/allbank")
@admin_required
def all_bank():
    ban=Balance.query.all()
    bank=[]
    for b in ban:
        bank.append({
            "bank_num":b.account_num,
            "bank":b.account_name,
            "user_id":b.user_bal,
            "bank_id":b.id,
            "user_balance":b.balance 
        })
    return jsonify({
        "all_bank_account_details":bank
    })

@v2_orders.route("/allorder")
@admin_required
def allorder():
    time.sleep(3)
    order=Order.query.all()
    if not order:
        jsonify("order not found") 
        return redirect(url_for("v1_orders.add_order"))
    ord=[]
    for o in order:
        ord.append({
            "id":o.id,
            "amount":o.amount,
            "product":o.product,
            "user_id":o.user_id
        }) 
    return ord 

@v2_orders.route("/ord_all")
@admin_required
def ord_all():
    cookies="product"
    cookies_data=current_redis.get(cookies)
    if cookies_data:
        return jsonify({
            "source":"cache",
            "dataset":json.loads(cookies_data)
        })
    product=allorder()
    current_redis.setex(cookies,6,json.dumps(product))
    return jsonify({
        "source":"database",
        "dataset":product
    })

@v2_orders.route("/delete_user/<int:id>",methods=["POST","GET"])
@jwt_required(locations=["cookies"])
def delete_user(id):
    current_user_id=int(get_jwt_identity())
    if current_user_id != id:
        return redirect(url_for("v2_orders.delete_user",id=current_user_id))
    user=User.query.get(id)
    if not user:
        return jsonify({"msg":"error user not found"})
    if request.method!="POST":
        return render_template("delete_user.html",user=user)
    email=request.form.get("email")
    du=User.query.filter_by(email=email).first()
    if not du:
        return jsonify({"error":"put correct user email"})
    db.session.delete(du)
    db.session.commit()
    flash("user id delete successfull")
    return redirect(url_for("v2_auth.signin_ui"))

@v2_orders.route("/delete_bank/<int:id>",methods=["POST","GET"])
@jwt_required(locations=["cookies"])
def delete_bank(id):
    current_user_id=int(get_jwt_identity())
    if current_user_id != id:
        return redirect(url_for("v2_orders.delete_bank",id=current_user_id))
    if request.method!="POST":
        return redirect("delete_bank",balance=balance)
    balance=Balance.query.filter_by(user_bal=id).first()
    if not balance:
        flash("balance id not found")
        return redirect(url_for("v2_orders.balance_add"))
    db.session.delete(balance)
    db.session.commit()
    flash("your balance id is deleted again new bank account add")
    return redirect(url_for("v2_orders.balance_add"))


@v2_orders.route("/alluser")
@admin_required
def alluser():
    user=User.query.limit(10).offset(20).all()
    row=[]
    if not user:
        return jsonify({"msg":"empty file"})
    for u in user:
        row.append({
            "id":u.id,
            "name":u.name,
            "email":u.email,
            "mobile":u.mobile,
            "role":u.role
        })
    return jsonify({
        "user":row
    })

@v2_orders.route("/make-admin/<int:id>",methods=["POST","GET"])
@jwt_required(locations=["cookies"])
@admin_required
def user_admin(id):
    user=User.query.get(id)
    if not user:
        return jsonify({"error":"user not found"})
    user.role="admin"
    db.session.commit()
    flash("user made admin ")
    return redirect(url_for("v2_orders.alluser")) 
@v2_orders.route("/dashboard")
@jwt_required(locations=["cookies"])
def dashboard():
    identety=int(get_jwt_identity())
    current_user_id=identety
    row=[]
    user=User.query.get(current_user_id)
    for o in user.orders:
        row.append({
            "product":o.product,
            "amount":o.amount,
            "id":o.id
        })      
    return jsonify({
        "user_id":user.id,
        "order":row,
        "name":user.name
    })
    

        