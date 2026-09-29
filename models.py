from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Table association pour les likes si tu l'as
# likes = db.Table('likes', ...)

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200), nullable=False)
    
    # INFOS SPORT PRO
    sport = db.Column(db.String(20), default='foot')  # foot / basket / handball
    poste = db.Column(db.String(50), default='Joueur')
    ville = db.Column(db.String(50), default='Danane')
    age = db.Column(db.Integer, default=19)
    bio = db.Column(db.Text, default='')
    photo_url = db.Column(db.String(500), default='')
    
    # STATS
    matchs = db.Column(db.Integer, default=0)
    buts = db.Column(db.Integer, default=0)
    
    # ABONNEMENT
    is_premium = db.Column(db.Boolean, default=False)
    is_club = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations
    posts = db.relationship('Post', backref='author', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.username}>'

class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    contenu = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500))
    sport = db.Column(db.String(20), default='foot')  # foot / basket / handball
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Post {self.id}>'

class Conversation(db.Model):
    __tablename__ = 'conversation'
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Pour afficher facilement
    user1 = db.relationship('User', foreign_keys=[user1_id])
    user2 = db.relationship('User', foreign_keys=[user2_id])

class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    conversation = db.relationship('Conversation', backref=db.backref('messages', lazy=True, order_by='Message.created_at'))
    sender = db.relationship('User')
