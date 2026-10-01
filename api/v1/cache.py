from flask import Blueprint,Flask,render_template,redirect,request,flash,session,jsonify
from models import Cachedata
from extensions import db

v1_cache=Blueprint("v1_cache",__name__)

    
@v1_cache.route("/addcache",methods=["GET"])
def addcache():
    if "user_id" not in session:
        return render_template("/login.html")
    return render_template("/cache.html")

@v1_cache.route("/savecache",methods=["POST"])
def savecache():
    if "user_id" not in session:
        return render_template("login.html")
    amount=request.form.get("amount")
    product=request.form.get("product")
    user=Cachedata(amount=amount,product=product,user_id=session["user_id"])
    db.session.add(user)
    db.session.commit()
    flash("Your data add cache")
    return render_template("/cache.html")

@v1_cache.route("/allcache", methods=["GET"])
def allcache():

    if "user_id" not in session:
        return render_template("login.html")

    orders = Cachedata.query.filter_by(
        user_id=session["user_id"]
    ).all()
    if orders is None:
        return jsonify({"user":"Not any cache data"}),404
    
    return jsonify([
        {
            "id": order.id,
            "amount": order.amount,
            "product": order.product
        }
        for order in orders
    ])