"""
MEET.FOOT - Models PRO
Architecture professionnelle, scalable, securisee
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum

db = SQLAlchemy()

class AccountType(str, Enum):
    PARTICULIER = "particulier"
    CLUB = "club"
    SCOUT = "scout"

class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(TimestampMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Profil
    type_compte = db.Column(db.String(20), default=AccountType.PARTICULIER.value, nullable=False)
    bio = db.Column(db.Text, default='')
    ville = db.Column(db.String(100), default='')
    poste = db.Column(db.String(50), default='')  # Attaquant, Milieu...
    photo_url = db.Column(db.String(500), default='')
    
    # Abonnement & Status
    is_active = db.Column(db.Boolean, default=True)
    is_premium = db.Column(db.Boolean, default=False)
    premium_until = db.Column(db.DateTime, nullable=True)
    
    # Relations
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password: str):
        if len(password) < 6:
            raise ValueError("Mot de passe trop court (min 6)")
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'type_compte': self.type_compte,
            'bio': self.bio,
            'photo_url': self.photo_url,
            'is_premium': self.is_premium
        }

    def __repr__(self):
        return f"<User {self.username}>"

class Post(TimestampMixin, db.Model):
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    contenu = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), default='')
    video_url = db.Column(db.String(500), default='')
    
    # Engagement
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    
    is_market = db.Column(db.Boolean, default=False, index=True)  # Si c'est une annonce market

    def __repr__(self):
        return f"<Post {self.id} by {self.user_id}>"

class MarketItem(TimestampMixin, db.Model):
    __tablename__ = 'market_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    titre = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    prix = db.Column(db.Float, nullable=True)
    categorie = db.Column(db.String(50), default='general')  # maillot, crampons, service...
    image_url = db.Column(db.String(500), default='')
    is_sold = db.Column(db.Boolean, default=False)
    
    seller = db.relationship('User', backref='market_items')

class Conversation(TimestampMixin, db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    user2_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Dernier message pour tri rapide
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        db.UniqueConstraint('user1_id', 'user2_id', name='unique_conversation'),
    )

class Message(TimestampMixin, db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    audio_url = db.Column(db.String(500), default='')
    image_url = db.Column(db.String(500), default='')
    
    conversation = db.relationship('Conversation', backref=db.backref('messages', lazy='dynamic', order_by='Message.created_at'))
    sender = db.relationship('User', backref='sent_messages')

class Notification(TimestampMixin, db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    type = db.Column(db.String(30), nullable=False)  # like, follow, message, market
    titre = db.Column(db.String(150), nullable=False)
    contenu = db.Column(db.Text, default='')
    link = db.Column(db.String(300), default='')
    is_read = db.Column(db.Boolean, default=False, index=True)

class Follow(TimestampMixin, db.Model):
    __tablename__ = 'follows'
    
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    __table_args__ = (
        db.UniqueConstraint('follower_id', 'followed_id', name='unique_follow'),
    )
