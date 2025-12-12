from database import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    subscription_level = db.Column(db.String(20), default='basic')
    account_status = db.Column(db.String(20), default='active')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Resource(db.Model):
    __tablename__ = 'resources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    access_level = db.Column(db.String(20), default='basic')
    available_hours_start = db.Column(db.String(5))
    available_hours_end = db.Column(db.String(5))

class Policy(db.Model):
    __tablename__ = 'policies'
    
    id = db.Column(db.Integer, primary_key=True)
    attribute = db.Column(db.String(100), nullable=False)
    operator = db.Column(db.String(20), nullable=False)
    value = db.Column(db.String(200), nullable=False)