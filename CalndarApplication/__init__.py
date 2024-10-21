from flask import Flask, request, session, redirect, jsonify
from dotenv import load_dotenv
import os
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.google import make_google_blueprint
from utils import db as database


def auth():
    print(request.path)
    if request.path.startswith("/static"):
        return

    if request.path == '/login' or request.path.startswith("/login/google"):
        return

    if request.path.startswith("/authorize"):
        return

    if request.path.startswith("/accounts"):
        return

    if request.path.startswith("/reset"):
        return

    user_info = session.get("user_info")
    if user_info:
        return
    print(request.url)
    return redirect('/login')


def create_app():
    app = Flask(__name__)

    load_dotenv()
    app.secret_key = os.getenv('PRIVATE_KEY')
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')

    # google auth

    blueprint = make_google_blueprint(
        client_id=client_id,
        client_secret=client_secret,
        scope=["https://www.googleapis.com/auth/userinfo.email",
               "https://www.googleapis.com/auth/userinfo.profile",
               "openid"],
        offline=True,
        reprompt_consent=True,
        redirect_to='authorize'
    )

    app.register_blueprint(blueprint, url_prefix="/login")

    @app.route('/login/google')
    def login_with_google():
        if not google.authorized:
            return redirect('/login')
        resp = google.get('/oauth2/v2/userinfo')

        if resp.status_code != 200:
            return f"Failed to fetch user info from Google: {resp.status_code}, {resp.text}"

        assert resp.ok
        email = resp.json()['email']
        print(email)

        user = database.fetch_one("select * from users where email=%s", [email])

        if user:
            session['user_id'] = user['userid']
            session["user_info"] = {'email': email}
            return jsonify({'success': True, 'message': 'Logged in successfully.'})
        else:
            # create a new client account
            params = [email, 'google-user']
            database.insert("insert into users (email, password) values (%s, %s)", params)
            user = database.fetch_one("select * from users where email=%s", [email])
            session['user_id'] = user['userid']
            session["user_info"] = {'email': email}
            return jsonify({'success': True, 'message': 'Logged in successfully.'})

    @app.route('/authorize')
    def authorize():
        if google.authorized:
            resp = google.get('/oauth2/v2/userinfo')
            print(resp.json())
            if resp.status_code == 200:
                email = resp.json().get('email')
                user = database.fetch_one("select * from users where email=%s", [email])
                if user:
                    session['user_id'] = user['userid']
                    session["user_info"] = {'email': email}
                else:
                    params = [email, 'google-user']
                    database.insert("insert into users (email, password) values (%s, %s)", params)
                    user = database.fetch_one("select * from users where email=%s", [email])
                    session['user_id'] = user['userid']
                    session["user_info"] = {'email': email}
            return redirect('/calendar')
        else:
            return redirect('/login')

    from .views import accounts, events
    app.register_blueprint(accounts.ac)
    app.register_blueprint(events.ev)

    app.before_request(auth)

    return app
