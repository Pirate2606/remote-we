from datetime import datetime
from flask import Flask
from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
db = SQLAlchemy()


class Sessions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(8))
    session_id = db.Column(db.Integer, unique=True)
    name = db.Column(db.String(256))
    desc = db.Column(db.Text)
    category = db.Column(db.String(256)) # Fun, Learning, Health
    url = db.Column(db.String(256))


class Register(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(8), unique=True)
    first_name = db.Column(db.String(256))
    last_name = db.Column(db.String(256))
    email = db.Column(db.String(256), unique=True)
    mobile_num = db.Column(db.String(20), unique=True)
    date = db.Column(db.DateTime, default=datetime.now())


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(8), unique=True)
    user_name = db.Column(db.String(256), unique=True)
    email = db.Column(db.String(256), unique=True)
    password = db.Column(db.String(256))

    def __init__(self, unique_id, user_name, email, password):
        self.unique_id = unique_id
        self.user_name = user_name
        self.email = email
        if password is not None:
            self.password = generate_password_hash(password)
        else:
            self.password = password

    def check_password(self, password):
        return check_password_hash(self.password, password)


login_manager = LoginManager()
login_manager.login_view = 'signup'


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))
