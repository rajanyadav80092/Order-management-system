from flask import Flask,jsonify,redirect,render_template,flash,Blueprint,request,session,url_for,json
from models import Order,Balance,db,User
from werkzeug.security import generate_password_hash,check_password_hash
import redis
import time
from sqlalchemy.exc import IntegrityError

client_redis=redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

v1_orders=Blueprint("v1_orders",__name__)

@v1_orders.route("/balance",methods=["POST","GET"])
def add_balance():
    if "user_id" not in session:
        return redirect("/login")
    if request.method=="POST":
        balance=request.form.get("balance")
        name=request.form.get("name")
        account_num=request.form.get("account_num")
        password=request.form.get("password")
        hashed=generate_password_hash(password)
        balance=Balance(balance=balance,account_num=account_num,password=hashed,user_bal=session["user_id"],account_name=name)
        db.session.add(balance)
        db.session.commit()
        flash("balance added in account successfully")
        return redirect("/addorder")
    return render_template("/balance.html")

@v1_orders.route("/add-balance/<int:id>",methods=["POST","GET"])
def add4_balance(id):
    if "user_id" not in session:
            return redirect("/login")
    if session["user_id"] != id:
            flash("INCORRECT USER ID")
            return redirect(url_for("v1_orders.add4_balance",id=session["user_id"]))
    bal=Balance.query.filter_by(user_bal=id).first()
    if not bal:
        flash("Account is not found")
        return redirect(url_for("v1_orders.add_balance"))
    if request.method=="POST":
        amou=request.form.get("amount")
        bal.balance+=int(amou)
        db.session.commit()
        flash({"success":"user balance update successfull"})
        return redirect("/addorder")
    return render_template("add_balance.html",bal=bal)

@v1_orders.route("/user-balance/<int:id>")
def user_balance(id):
    if "user_id" not in session:
        return redirect("/login")
    
    if session["user_id"] != id:
        return redirect(url_for("v1_orders.user_balance",id=session["user_id"]))
    balance=Balance.query.filter_by(user_bal=id).first()
    if not balance:
        flash("balance id not found ")
        return redirect(url_for("v1_orders.add_balance"))
    return jsonify({
        "id":balance.id,
        "balance":balance.balance,
        "account_num":balance.account_num,
        "bank_user_id":balance.user_bal,
        "user_bank name":balance.account_name
    })


@v1_orders.route("/add-order",methods=["POST","GET"])
def add_order():
    if "user_id" not in session:
        return redirect("/login")
    if request.method=="POST":
        product=request.form.get("product")
        try:
            amount = int(request.form.get("amount"))
        except (TypeError, ValueError):
            db.session.rollback()
            flash("Invalid amount")
            return redirect(url_for("v1_orders.add_order"))
        id=session["user_id"]
        bala=Balance.query.filter_by(user_bal=id).first()
        if not bala:
            flash("Balance account not found")
            return redirect(url_for("v1_orders.add_balance"))
        if bala.balance < amount:
            flash("please check your bank balance")
            return redirect(url_for("v1_orders.add4_balance",id=session["user_id"]))
        
        try:
            bala.balance-=amount
            order=Order(product=product,amount=amount,user_id=session["user_id"])
            db.session.add(order)
            db.session.add(bala)
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

        flash("Your order added successfully")
        return redirect(url_for("v1_orders.add_order"))
    return redirect("/addorder")

@v1_orders.route("/user/<int:id>/order")
def user_order(id):
    if "user_id" not in session:
        return redirect("/login")
    if session["user_id"] != id:
        return redirect(url_for("v1_orders.user_order",id=session["user_id"]))
    row=[]
    user=User.query.get(id)
    for o in user.orders:
        row.append({
            "id":o.id,
            "product":o.product,
            "amount":o.amount
        })
    return jsonify({
        "allorder":row,
        "user_id":user.id,
        "name":user.name,
    })
@v1_orders.route("/order/<int:id>/user")
def order_user(id):
    if "user_id" not in session:
        return redirect("/login")
    order=Order.query.get(id)
    return jsonify({
        "id":order.id,
        "product":order.product,
        "amount":order.amount,
        "user_name":order.user.name,
        "user_id":order.user_id
    })
    
@v1_orders.route("/alluser")
def alluser():
    if "user_id" not in session:
        return redirect("/login")
    time.sleep(3)
    userall=User.query.all()
    row=[]
    for u in userall:
        row.append({
            "user_id":u.id,
            "name":u.name,
            "email":u.email,
            "mobile":u.mobile,
            "password":u.password,
            "role":u.role
        })
    return row
@v1_orders.route("/alluse")
def userall():
    
    cache_key="product"
    cache_data=client_redis.get(cache_key)
    if cache_data:
        return jsonify({
            "source":"cache",
            "dataset":json.loads(cache_data)
        })
    product=alluser()
    client_redis.setex(cache_key,6,json.dumps(product))
    return jsonify({
        "source":"database",
        "dataset":product
    })
    
@v1_orders.route("/allorder")
def allorder():
    if "user_id" not in session:
        return redirect("/login")
    ordd=Order.query.all()
    rowo=[]
    for o in ordd:
        rowo.append({
            "product":o.product,
            "amount":o.amount,
            "order_id":o.id,
            "order_user":o.user.name,
            "user_id":o.user_id
        })
    return jsonify({
        "order":rowo
    })

@v1_orders.route("/delete_user/<int:id>",methods=["DELETE","GET"])
def delete_user(id):
    if "user_id" not in session:
        return redirect("/login")
    if session["user_id"] != id:
        return redirect(url_for("v1_orders.delete_user",id=session["user_id"])) 
    delete_us=User.query.get(id)
    db.session.delete(delete_us)
    db.session.commit()
    flash(f"user delete  id:{id} successfull")
    return redirect("/login")

@v1_orders.route("/delete_order/<int:id>",methods=["POST","GET"])
def delete_order(id):
    if "user_id" not in session:
        return redirect("/login")
    order=Order.query.get(id)
    if not order:
        flash("order id not found")
        return redirect(url_for("v1_orders.allorder"))
    db.session.delete(order)
    db.session.commit()
    flash("your order is remove")
    return redirect("/addorder")

@v1_orders.route("delete_bank/<int:id>",methods=["DELETE","GET"])
def delete_bank(id):
    if "user_id" not in session:
        return redirect("/login")
    if session["user_id"] != id:
        flash("your only delete her account")
        return redirect(url_for("v1_orders.delete_bank",id=session["user_id"]))
    balanc=Balance.Query.get(id)
    db.session.delete(balanc)
    db.session.commit()
    flash("user bank account deleted successfully")
    return redirect("/balance")
    
@v1_orders.route("/make-admin",methods=["POST","GET"])
def make_admin():
    if session["user_role"]!="admin":
        flash("only admin can make admin")
        return
    if request.method=="POST":
        email=request.form.get("email")
        user=User.query.filter_by(email=email).first()
        if user:
            user.role="admin"
            db.session.commit()
            flash("user role update successfull")
            return redirect("/addorder")
        flash("email id is not correct please put correct id")
        return redirect(url_for("v1_orders.make_admin"))
    return render_template("admin.html")
        
@v1_orders.route("/settings")
def settings():
    if "user_id" not in session:
        flash("your id not first login then settings")
        return redirect("/login")
    id=session["user_id"]
    user = User.query.get(id)
    return render_template("settings.html", user=user)  
            
        