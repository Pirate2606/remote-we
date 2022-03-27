import os
import re
import string
import uuid
import bleach
import random

from flask import render_template, request, redirect, url_for, g, session, abort, flash
from flask_login import login_user, logout_user, login_required, current_user
from wtforms import ValidationError

from cli import create_db
from config import Config
from models import app, db, Users, login_manager, Register, Sessions
from sendMail import send_mail


app.config.from_object(Config)
app.cli.add_command(create_db)
db.init_app(app)
login_manager.init_app(app)


@app.route('/')
def home():
    if not session.get('user_id'):
        return render_template("home.html")
    else:
        unique_id = Users.query.filter_by(
            id=session['user_id']).first().unique_id
        if Register.query.filter_by(unique_id=unique_id).first() is None:
            return redirect(url_for("registration_form", unique_id=unique_id))
        return render_template("home.html", unique_id=unique_id)


@app.route('/<unique_id>/create', methods=["GET", "POST"])
@login_required
def create(unique_id):
    category_dict = {
        'Fun': 'fun',
        'Health': 'health',
        'Learn': 'learn'
    }
    if not session.get('user_id'):
        return redirect(url_for('signup'))
    elif Users.query.filter_by(id=session.get('user_id')).first().unique_id != unique_id:
        abort(403)
    if Register.query.filter_by(unique_id=unique_id).first() is None:
        return redirect(url_for("registration_form", unique_id=unique_id))
    allowed_tags =  [
        'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'strong', 'ul', 'h1', 'br', 'h2', 'h3', 
        'h4', 'h5', 'h6', 'u', 'font', 'span', 'p']
    register = Register.query.filter_by(unique_id=unique_id).first()
    registration_id = register.email.split("@")[0]
    if request.method == "POST":
        session_ = Sessions()
        session_.unique_id = unique_id
        session_.session_id = random.randint(0, 999999)
        session_.name = request.form["title"]
        session_.url = request.form["url"]
        session_.desc = bleach.clean(request.form["description"], tags=allowed_tags)
        session_.category = category_dict[request.form["type"]]
        db.session.add(session_)
        db.session.commit()
        return redirect(url_for("sessions", category=category_dict[request.form["type"]]))
    return render_template('create_session.html', unique_id=unique_id, registration_id=registration_id)


@app.route('/sessions/<category>', methods=["GET", "POST"])
def sessions(category):
    sessions_ = Sessions()
    all_items = sessions_.query.filter_by(category=category).all()
    total_items = len(all_items)
    number_of_rows = (total_items // 3) + 1
    user_names = []

    for item in all_items:
        user_names.append(Users.query.filter_by(
            unique_id=item.unique_id).first().user_name)

    if request.method == "POST":
        if not session.get('user_id'):
            return redirect(url_for('signup'))
        else:
            unique_id = Users.query.filter_by(
                id=session['user_id']).first().unique_id
    if not session.get('user_id'):
        return render_template('sessions.html',
                               all_items=all_items,
                               number_of_rows=number_of_rows,
                               total_items=total_items,
                               category=category,
                               user_names=user_names)
    else:
        unique_id = Users.query.filter_by(
            id=session['user_id']).first().unique_id
        if Register.query.filter_by(unique_id=unique_id).first() is None:
            return redirect(url_for("registration_form", unique_id=unique_id))
        return render_template('sessions.html',
                               all_items=all_items,
                               number_of_rows=number_of_rows,
                               total_items=total_items,
                               category=category,
                               unique_id=Users.query.filter_by(
                               id=session['user_id']).first().unique_id,
                               user_names=user_names)


@app.route('/learn_sessions')
def learn_sessions():
    return {"success": True}


@app.route('/fun_sessions')
def fun_sessions():
    return {"success": True}


@app.route('/health_sessions')
def health_sessions():
    return {"success": True}


@app.route('/<unique_id>/profile')
@login_required
def profile(unique_id):
    if not session.get('user_id'):
        return redirect(url_for('signup'))
    elif Users.query.filter_by(id=session.get('user_id')).first().unique_id != unique_id:
        abort(403)
    if Register.query.filter_by(unique_id=unique_id).first() is None:
        return redirect(url_for("registration_form", unique_id=unique_id))
    register = Register.query.filter_by(unique_id=unique_id).first()
    registration_id = register.email.split("@")[0]
    registration_date = register.date.strftime("%d-%m-%Y")
    registration_time = register.date.strftime("%H:%M:%S")
    sessions_ = Sessions.query.filter_by(unique_id=unique_id).all()
    return render_template("profile.html",
                           register=register,
                           registration_id=registration_id,
                           unique_id=unique_id,
                           registration_time=registration_time,
                           registration_date=registration_date,
                           sessions_=sessions_)


@app.route('/<unique_id>/register', methods=['POST', 'GET'])
@login_required
def registration_form(unique_id):
    email = Users.query.filter_by(unique_id=unique_id).first().email
    if request.method == "POST":
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        mobile_num = request.form['mobile_num']
        if Register.query.filter_by(mobile_num=mobile_num).first() is not None:
            flash('This mobile number is already registered with some other account.')
            return redirect(url_for("registration_form", unique_id=unique_id))
        register = Register(unique_id=unique_id,
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            mobile_num=mobile_num,
                            )
        db.session.add(register)
        db.session.commit()
        return redirect(url_for('profile', unique_id=unique_id))
    return render_template('registration-form.html', email=email)


@app.route("/check_login")
@login_required
def check_login():
    g.user = current_user.get_id()
    if g.user:
        user_id = int(g.user)
        user = Users.query.get(user_id)
        unique_id = user.unique_id
        has_registered = Register.query.filter_by(unique_id=unique_id).first()
        if has_registered is not None:
            return redirect(url_for('home'))
        return redirect(url_for('registration_form', unique_id=unique_id))


@app.route('/sign_up', methods=['GET', 'POST'])
def signup():
    if session.get("user_id"):
        return redirect(url_for('home'))
    email_flag = False
    username_flag = False
    password_flag = False

    if request.method == "POST":
        user_name = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_flag = check_password(password)
        try:
            email_flag = check_mail(email)
        except ValidationError:
            email_flag = True

        try:
            username_flag = check_username(user_name)
        except ValidationError:
            username_flag = True

        if not username_flag and not email_flag and not password_flag and password_flag != "short":
            # Entering data into Database (Register table)
            unique_id = uuid.uuid4().hex[:8]
            user = Users(unique_id, user_name, email, password)
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            login_user(user)

            return redirect(url_for('check_login'))

    return render_template('sign-up.html',
                           email_flag=email_flag,
                           username_flag=username_flag,
                           password_flag=password_flag)


@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    if session.get("user_id"):
        return redirect(url_for('home'))
    flag = False
    if request.method == "POST":
        user = Users.query.filter_by(email=request.form['username']).first()
        if user is None:
            user = Users.query.filter_by(
                user_name=request.form['username']).first()
        if user is not None:
            if user.check_password(request.form['password']):
                user = Users.query.filter_by(email=user.email).first()
                session['user_id'] = user.id
                login_user(user)
                return redirect(url_for("home"))
            else:
                flag = True
        else:
            flag = True
    return render_template('sign-in.html', flag=flag)


@app.route("/logout")
@login_required
def logout():
    session.pop('user_id', None)
    logout_user()
    return redirect(url_for("home"))


@app.route('/contact_us', methods=["GET", "POST"])
def contact_us():
    if request.method == "POST":
        name = request.form['txtName']
        email = request.form['txtEmail']
        phone = request.form['txtPhone']
        msg = request.form['txtMsg']
        send_mail(name, email, phone, msg)
    if not session.get('user_id'):
        return render_template('contact-us.html')
    else:
        return render_template('contact-us.html',
                               unique_id=Users.query.filter_by(
                                id=session.get('user_id')).first().unique_id)


@app.route('/about_us')
def about_us():
    if not session.get('user_id'):
        return render_template('about-us.html')
    else:
        return render_template('about-us.html',
                            unique_id=Users.query.filter_by(
                            id=session.get('user_id')).first().unique_id)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(403)
def page_not_found(error):
    return render_template('403.html'), 403


# Functions
def check_mail(data):
    if Users.query.filter_by(email=data).first():
        raise ValidationError('Your email is already registered.')
    else:
        return False


def check_username(data):
    if Users.query.filter_by(user_name=data).first():
        raise ValidationError('This username is already registered.')
    else:
        return False


def check_password(data):
    special_char = string.punctuation
    if len(data) < 6:
        return "short"
    elif not re.search("[a-zA-Z]", data):
        return True
    elif not re.search("[0-9]", data):
        return True
    for char in data:
        if char in special_char:
            break
    else:
        return True
    return False


if __name__ == '__main__':
    app.run(debug=True)