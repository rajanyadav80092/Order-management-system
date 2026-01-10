from extensions import db

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),nullable=False)
    email=db.Column(db.String(200),unique=True,nullable=False)
    password=db.Column(db.String(200),nullable=False)
    mobile=db.Column(db.Integer,nullable=False)
    role=db.Column(db.String(200),default="user",nullable=False)
    orders=db.relationship("Order",backref="user",lazy=True,cascade="all,delete-orphan")
    balance=db.relationship("Balance",backref="user",lazy=True,cascade="all,delete-orphan")

class Order(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    product=db.Column(db.String(200),nullable=False)
    amount=db.Column(db.Integer,nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)
    
    
class Balance(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    account_name=db.Column(db.String(200),nullable=False)
    account_num=db.Column(db.Integer,nullable=False)
    password=db.Column(db.String(200),nullable=False)
    balance=db.Column(db.BigInteger,nullable=False)
    user_bal=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)
    
class PasswordReset(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)
    token=db.Column(db.String(200),unique=True,nullable=False)
    expires_at=db.Column(db.DateTime,nullable=False)