from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

from models import db, User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'meet-foot-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meetfoot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- ROUTES ----------------
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('accueil'))
    return '''
    <!doctype html>
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Meet Foot</title></head>
    <body style="margin:0;font-family:sans-serif;background:linear-gradient(135deg,#ff00aa,#7c3aed);min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;color:white">
    <div style="padding:20px">
    <h1 style="font-size:42px;font-weight:900;margin:0">⚽ MEET FOOT</h1>
    <p style="font-size:18px;opacity:0.9;margin:16px 0 32px">Trouve ton match, ton équipe, ton terrain</p>
    <div style="display:flex;flex-direction:column;gap:14px;max-width:320px;margin:0 auto">
    <a href="/login" style="background:white;color:#c026d3;padding:16px;border-radius:30px;text-decoration:none;font-weight:700;font-size:18px">Connexion</a>
    <a href="/inscription_particulier" style="background:rgba(0,0,0,0.25);border:2px solid white;color:white;padding:16px;border-radius:30px;text-decoration:none;font-weight:700;font-size:18px">Inscription Joueur</a>
    <a href="/inscription_club" style="background:rgba(255,255,255,0.15);border:2px solid white;color:white;padding:16px;border-radius:30px;text-decoration:none;font-weight:700;font-size:18px">Inscription Club</a>
    </div>
    </div>
    </body></html>
    '''