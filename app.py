from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

from models import db, User, Post, MarketItem, Conversation, Message, Notification, AccountType

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'meet-sport-secret-danané-2026')
# Utilise SQLite pour que ça marche sans shell payant
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///meet.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Init DB
db.init_app(app)

# Login Manager
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
    # FIX: pas besoin de template, on affiche direct
    return '''
    <!doctype html>
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Meet Foot Danané</title></head>
    <body style="font-family:sans-serif;text-align:center;padding:30px;background:#0f172a;color:white">
    <h1 style="font-size:32px">⚽ MEET FOOT DANANÉ</h1>
    <p>Plateforme multi-sport de Danané</p>
    <div style="margin-top:30px">
    <a href="/login" style="background:#22c55e;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;margin:5px;display:inline-block">Connexion</a>
    <a href="/inscription_particulier" style="background:#3b82f6;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;margin:5px;display:inline-block">Inscription Joueur</a>
    <a href="/inscription_club" style="background:#f59e0b;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;margin:5px;display:inline-block">Club</a>
    </div>
    <p style="margin-top:40px;opacity:0.6">Site en ligne ✅</p>
    </body></html>
    '''

@app.route('/accueil', methods=['GET', 'POST'])
@login_required
def accueil():
    if request.method == 'POST':
        contenu = request.form.get('contenu')
        sport = request.form.get('sport', 'foot')
        image_url = request.form.get('image_url')
        if contenu:
            post = Post(contenu=contenu, sport=sport, image_url=image_url, user_id=current_user.id)
            db.session.add(post)
            db.session.commit()
            return redirect(url_for('accueil'))
    
    sport_filter = request.args.get('sport')
    q = request.args.get('q')
    
    query = Post.query.order_by(Post.created_at.desc())
    if sport_filter:
        query = query.filter_by(sport=sport_filter)
    if q:
        query = query.filter(Post.contenu.contains(q))
    
    posts = query.all()
    return render_template('accueil.html', posts=posts)

@app.route('/market')
@login_required
def market():
    sport_filter = request.args.get('sport')
    q = request.args.get('q')
    
    query = User.query
    if sport_filter:
        query = query.filter_by(sport=sport_filter)
    if q:
        query = query.filter(User.username.contains(q))
    
    users = query.order_by(User.created_at.desc()).all()
    return render_template('market.html', users=users)

@app.route('/profil/<username>')
@login_required
def profil(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    return render_template('profil.html', user_profile=user, posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('accueil'))
        flash('Identifiants incorrects')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/inscription_particulier', methods=['GET', 'POST'])
def inscription_particulier():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        sport = request.form.get('sport', 'foot')
        ville = request.form.get('ville', 'Danane')
        
        if User.query.filter_by(username=username).first():
            flash('Nom deja pris')
            return redirect(url_for('inscription_particulier'))
        
        hashed = generate_password_hash(password)
        user = User(username=username, email=email, password=hashed, sport=sport, ville=ville, account_type=AccountType.PARTICULIER)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('accueil'))
    return render_template('inscription_particulier.html')

@app.route('/inscription_club', methods=['GET', 'POST'])
def inscription_club():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        sport = request.form.get('sport', 'foot')
        
        if User.query.filter_by(username=username).first():
            flash('Nom deja pris')
            return redirect(url_for('inscription_club'))
        
        hashed = generate_password_hash(password)
        user = User(username=username, email=email, password=hashed, sport=sport, ville='Danane', account_type=AccountType.CLUB)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('accueil'))
    return render_template('inscription_club.html')

@app.route('/abonnement')
@login_required
def abonnement():
    return render_template('abonnement.html')

@app.route('/nouvelle_conversation')
@login_required
def nouvelle_conversation():
    to = request.args.get('to')
    return redirect(url_for('market'))

# FIX SANS SHELL PAYANT - Creation auto des tables
with app.app_context():
    db.create_all()
    print("DB OK - Tables creees")