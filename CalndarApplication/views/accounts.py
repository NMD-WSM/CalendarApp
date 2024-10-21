import secrets
import smtplib
from email.mime.text import MIMEText
from flask_dance.contrib.google import make_google_blueprint, google
import configparser

import pymysql
from flask import Blueprint, render_template, request, redirect, session, jsonify
from utils import db
from datetime import datetime, timedelta

ac = Blueprint("account", __name__)


@ac.route('/')
def home():
    return redirect('/login')


@ac.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")

    request_email = request.form.get('email')
    request_password = request.form.get('password')

    # connect to database
    user_dict = db.fetch_one("select * from users where email=%s and password=%s", [request_email, request_password])

    if user_dict:
        session["user_info"] = {'email': request_email, 'id': user_dict['userid']}
        return redirect('/calendar')
    return render_template("login.html", error="User name or password is incorrect!")


@ac.route('/accounts/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    registered = db.fetch_one("select * from users where email=%s", [email])
    print(registered)
    if registered:
        return jsonify({'success': False, 'message': 'Email already registered.'}), 400
    params = [email, password]
    print(params)
    db.insert("insert into users(email, password) values (%s,%s)", params)
    return jsonify({'success': True, 'message': 'User registered successfully.'}), 200


@ac.route('/accounts/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')

    registered = db.fetch_one("select * from users where email=%s", [email])
    if not registered:
        return jsonify({'success': False, 'message': 'Email not found.'}), 404
    reset_token = secrets.token_urlsafe(16)
    reset_expiration = datetime.now() + timedelta(hours=24)
    params = [reset_token, reset_expiration, email]
    db.update("update users set reset_token=%s, reset_expiration=%s WHERE email=%s", params)

    # send email to rest password
    config = configparser.ConfigParser()
    config.read('config.ini')

    sender_email = config.get('SMTP', 'sender_email')
    sender_password = config.get('SMTP', 'sender_password')

    msg = MIMEText(f"Click the following link to reset your password: http://127.0.0.1:5000//reset/{reset_token}")
    msg['Subject'] = 'Password Reset Request'
    msg['From'] = sender_email
    msg['To'] = email

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, [email], msg.as_string())
    server.quit()

    return jsonify({'success': True, 'message': 'Reset link sent to your email.'})


@ac.route('/reset/<token>')
def show_reset_form(token):

    valid_token = db.fetch_one("select * from users where reset_token=%s and reset_expiration > NOW()", (token,))
    if not valid_token:
        return jsonify({'success': False, 'message': 'Invalid or expired token.'}), 400
    return render_template('reset_password.html', token=token)


@ac.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')

    valid_token = db.fetch_one("select * from users where reset_token=%s and reset_expiration > NOW()", (token,))
    if not valid_token:
        return jsonify({'success': False, 'message': 'Invalid or expired token.'}), 400

    params = [new_password, token]
    db.update("update users set password=%s, reset_token=NULL, reset_expiration=NULL WHERE reset_token=%s", params)
    return jsonify({'success': True, 'message': 'Password reset successfully.'})

