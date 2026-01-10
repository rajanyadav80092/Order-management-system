from flask import Flask,render_template,redirect,session
from config import Config
from extensions import db,jwt
from models import User

from api.v1.auth import v1_auth
from api.v1.orders import v1_orders
from api.v1.update import v1_update
from api.v2.auth import v2_auth
from api.v2.orders import v2_orders
from api.v2.update import v2_update
from flask_mail import Mail, Message

app=Flask(__name__)

app.config.from_object(Config)

app.config["JWT_TOKEN_LOCATION"]=["cookies"]
app.config["JWT_COOKIE_CSRF_PROTECT"]=False
app.config["JWT_COOKIE_SECURE"] = False
app.config["JWT_REFRESH_COOKIE_NAME"]="refresh_token_cookie"
app.config["JWT_ACCESS_COOKIE_NAME"]="access_token_cookie"

app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME="your_email@gmail.com",
    MAIL_PASSWORD="your_app_password"
)

mail = Mail(app)




db.init_app(app)
jwt.init_app(app)

app.register_blueprint(v1_auth,url_prefix="/api/v1")
app.register_blueprint(v1_orders,url_prefix="/api/v1")
app.register_blueprint(v1_update,url_prefix="/api/v1")
app.register_blueprint(v2_auth,url_prefix="/api/v2")
app.register_blueprint(v2_orders,url_prefix="/api/v2")
app.register_blueprint(v2_update,url_prefix="/api/v2")


@jwt.expired_token_loader
def expired_token_callback(jwt_header,jwt_payload):
    return redirect("/api/v2/refresh")

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/signin")
def signin():
    return render_template("signin.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/addorder")
def addorder():
    return render_template("add_order.html")

@app.route("/balance")
def balance():
    return render_template("balance.html")

@app.route("/forget")
def forget():
    return render_template("forget.html")

if __name__== ("__main__"):
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    