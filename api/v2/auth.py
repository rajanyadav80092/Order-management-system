from flask import Flask,redirect,render_template,flash,json,jsonify,Blueprint,request,url_for,make_response,flash
from flask_jwt_extended import get_jwt_identity,create_access_token,jwt_required,create_refresh_token

from werkzeug.security import generate_password_hash,check_password_hash
from extensions import db
from models import User
from sqlalchemy import or_

v2_auth=Blueprint("v2_auth",__name__)

@v2_auth.route("/signin",methods=["POST","GET"])
def signin_ui():
    if request.method=="POST":
        name=request.form.get("name")
        email=request.form.get("email")
        mobile=request.form.get("mobile")
        password=request.form.get("password")
        
        hashed=generate_password_hash(password)
        user=User(name=name,email=email,password=hashed,mobile=mobile)
        db.session.add(user)
        db.session.commit()
        flash("user added successfull")
        return redirect("/login")
    return render_template("signin.html")

@v2_auth.route("/login",methods=["POST","GET"])
def login_ui():
    if request.method=="POST":
        identifier=request.form.get("identifier")
        password=request.form.get("password")
        user=User.query.filter(or_(User.name==identifier,
                                   User.email==identifier,
                                   User.mobile==identifier)).first()
        
        if not user:
            flash("user is not found")
            return redirect(url_for("v2_auth.login_ui"))
        if user and check_password_hash(user.password,password):
            access_token=create_access_token(
                identity=str(user.id),
                additional_claims={"role":user.role}
            )
            refresh_token=create_refresh_token(
                identity=str(user.id),
                additional_claims={"role":user.role}
            )
            resp=make_response(redirect("/addorder"))
            resp.set_cookie(
                "access_token_cookie",
                access_token,
                httponly=True,
                samesite="Lax",
                path="/",
                secure=True
            )
            resp.set_cookie(
                "refresh_token_cookie",
                refresh_token,
                httponly=True,
                samesite="Lax",
                path="/",
                secure=True
            )
            flash("user login successfull")
            return resp
        return jsonify({"error":"please check your password"})
    return render_template("login.html")

@v2_auth.route("/refresh",methods=["POST","GET"])
@jwt_required(refresh=True,locations=["cookies"])
def refresh_ui():
    user_id=int(get_jwt_identity())
    new_access=create_access_token(identity=str(user_id))
    resp= jsonify({"msg":"token refreshed"})
    resp.set_cookie(
        "access_token_cookie",
        new_access,
        path="/",
        samesite="Lax",
        httponly=True,
        secure=True
    )
    
    return resp

@v2_auth.route("/admin/make-admin/<int:user_id>",methods=["POST","GET"])
@jwt_required(locations=["cookies"])
def make_admin(user_id):
    current_user_id=get_jwt_identity()
    current_user=User.query.get(current_user_id)

    #only admin can do this
    if current_user.role != "admin":
        return jsonify({"error":"Admin access required"}),403
    user=User.query.get(user_id)
    if not user:
        return jsonify({"error":"user not found"}),404
    user.role="admin"
    db.session.commit()
    return jsonify({
        "msg":f"{user.name} is now an admin"
    })
    
@v2_auth.route("/logout")
@jwt_required(locations=["cookies"])
def logout():
    responses=make_response(redirect("/login"))
    responses.delete_cookie("access_token_cookie")
    return responses


