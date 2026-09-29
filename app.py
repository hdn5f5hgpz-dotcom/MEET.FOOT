"""
MEET.FOOT - App PRO
Production-ready | Securise | Scalable | Render compatible
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
from models import db, User, Post, MarketItem, Conversation, Message, Notification, AccountType
from functools import wraps
from datetime import datetime, timedelta
import os
import logging

# --- CONFIG ---
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'meetfoot-pro-2026-secure-key-change-in-prod')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'meetfoot_pro.db')
    # Fix pour Render Postgres
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Init DB
    db.init_app(app)
    
    # Logging pro
    logging.basicConfig(level=logging.INFO)
    app.logger.info("MEET.FOOT PRO demarre...")

    # Creation tables
    with app.app_context():
        db.create_all()
        app.logger.info("Base de donnees prete")

    # --- SECURITE & HELPERS ---
    @app.before_request
    def make_session_permanent():
        session.permanent = True

    def login_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                flash('Veuillez vous connecter', 'warning')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated

    def get_current_user():
        if 'user_id' in session:
            return User.query.get(session['user_id'])
        return None

    @app.context_processor
    def inject_user():
        """Rend current_user disponible dans tous les templates"""
        return dict(current_user=get_current_user(), now=datetime.utcnow())

    # --- GESTION D'ERREURS PRO ---
    @app.errorhandler(404)
    def not_found(e):
        return render_template('acces_refuse.html', error="Page introuvable (404)"), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template('acces_refuse.html', error="Erreur serveur (500)"), 500

    # --- ROUTES AUTH ---
    @app.route('/', methods=['GET'])
    def index():
        if 'user_id' in session:
            return redirect(url_for('accueil'))
        # Stats pour landing page
        total_users = User.query.count()
        total_posts = Post.query.count()
        return render_template('index.html', stats={'users': total_users, 'posts': total_posts})

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if 'user_id' in session:
            return redirect(url_for('accueil'))
        
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            
            if not username or not password:
                flash('Tous les champs sont requis', 'danger')
                return render_template('login.html')
            
            user = User.query.filter((User.username == username) | (User.email == username)).first()
            
            if user and user.check_password(password):
                if not user.is_active:
                    flash('Compte desactive', 'danger')
                    return render_template('login.html')
                session['user_id'] = user.id
                session['username'] = user.username
                session['type_compte'] = user.type_compte
                app.logger.info(f"Login: {user.username}")
                return redirect(url_for('accueil'))
            else:
                flash('Identifiants incorrects', 'danger')
        
        return render_template('login.html')

    @app.route('/inscription_particulier', methods=['GET', 'POST'])
    def inscription_particulier():
        return handle_inscription(AccountType.PARTICULIER.value)

    @app.route('/inscription_club', methods=['GET', 'POST'])
    def inscription_club():
        return handle_inscription(AccountType.CLUB.value)

    def handle_inscription(type_compte):
        if 'user_id' in session:
            return redirect(url_for('accueil'))
        
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '').strip()
            password_confirm = request.form.get('password_confirm', '').strip()

            # Validation pro
            if not all([username, email, password]):
                flash('Tous les champs obligatoires', 'danger')
                return render_template(f'inscription_{type_compte}.html')
            if len(username) < 3:
                flash('Pseudo trop court (min 3)', 'danger')
                return render_template(f'inscription_{type_compte}.html')
            if password != password_confirm and password_confirm != '':
                flash('Mots de passe differents', 'danger')
                return render_template(f'inscription_{type_compte}.html')
            if len(password) < 6:
                flash('Mot de passe min 6 caracteres', 'danger')
                return render_template(f'inscription_{type_compte}.html')
            
            if User.query.filter_by(username=username).first():
                flash('Ce pseudo est deja pris', 'danger')
                return render_template(f'inscription_{type_compte}.html')
            if User.query.filter_by(email=email).first():
                flash('Cet email est deja utilise', 'danger')
                return render_template(f'inscription_{type_compte}.html')

            try:
                user = User(username=username, email=email, type_compte=type_compte)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                
                session['user_id'] = user.id
                session['username'] = user.username
                session['type_compte'] = user.type_compte
                flash(f'Bienvenue {username} !', 'success')
                app.logger.info(f"Nouvel utilisateur: {username} ({type_compte})")
                return redirect(url_for('accueil'))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Erreur inscription: {e}")
                flash('Erreur lors de la creation du compte', 'danger')
        
        return render_template(f'inscription_{type_compte}.html')

    @app.route('/logout')
    def logout():
        session.clear()
        flash('Deconnexion reussie', 'info')
        return redirect(url_for('index'))

    # --- FEED / ACCUEIL ---
    @app.route('/accueil', methods=['GET', 'POST'])
    @login_required
    def accueil():
        user = get_current_user()
        
        if request.method == 'POST':
            contenu = request.form.get('contenu', '').strip()
            image_url = request.form.get('image_url', '').strip()
            
            if not contenu:
                flash('Le contenu ne peut pas etre vide', 'warning')
            elif len(contenu) > 2000:
                flash('Post trop long (max 2000)', 'warning')
            else:
                post = Post(user_id=user.id, contenu=contenu, image_url=image_url)
                db.session.add(post)
                db.session.commit()
                flash('Publie !', 'success')
                return redirect(url_for('accueil'))

        # Pagination pro
        page = request.args.get('page', 1, type=int)
        posts = Post.query.filter_by(is_market=False)\
            .order_by(Post.created_at.desc())\
            .paginate(page=page, per_page=20, error_out=False)
        
        return render_template('accueil.html', posts=posts, user=user)

    @app.route('/creer', methods=['GET', 'POST'])
    @login_required
    def creer():
        return redirect(url_for('accueil'))

    # --- MARKET ---
    @app.route('/market')
    @login_required
    def market():
        page = request.args.get('page', 1, type=int)
        posts = Post.query.filter_by(is_market=True).order_by(Post.created_at.desc())\
            .paginate(page=page, per_page=20, error_out=False)
        items = MarketItem.query.order_by(MarketItem.created_at.desc()).limit(20).all()
        return render_template('market.html', posts=posts, items=items)

    @app.route('/market_publier', methods=['GET', 'POST'])
    @login_required
    def market_publier():
        user = get_current_user()
        if request.method == 'POST':
            titre = request.form.get('titre', '').strip() or request.form.get('contenu', '').strip()[:50]
            description = request.form.get('description', '').strip() or request.form.get('contenu', '').strip()
            prix = request.form.get('prix', type=float)
            image_url = request.form.get('image_url', '').strip()
            
            if description:
                # Creation Post Market + MarketItem
                post = Post(user_id=user.id, contenu=description, image_url=image_url, is_market=True)
                db.session.add(post)
                
                item = MarketItem(user_id=user.id, titre=titre, description=description, prix=prix, image_url=image_url)
                db.session.add(item)
                db.session.commit()
                flash('Annonce publiee sur le Market !', 'success')
                return redirect(url_for('market'))
        
        return render_template('market_publier.html')

    # --- MESSAGERIE ---
    @app.route('/messagerie')
    @login_required
    def messagerie():
        user = get_current_user()
        conversations = Conversation.query.filter(
            (Conversation.user1_id == user.id) | (Conversation.user2_id == user.id)
        ).order_by(Conversation.last_message_at.desc()).all()
        
        # Enrichir avec l'autre utilisateur
        convos_data = []
        for c in conversations:
            other_id = c.user2_id if c.user1_id == user.id else c.user1_id
            other_user = User.query.get(other_id)
            last_msg = c.messages.order_by(Message.created_at.desc()).first()
            convos_data.append({'conv': c, 'other': other_user, 'last_msg': last_msg})
        
        return render_template('messagerie.html', conversations=convos_data, user=user)

    @app.route('/nouvelle_conversation')
    @login_required
    def nouvelle_conversation():
        user = get_current_user()
        users = User.query.filter(User.id != user.id).order_by(User.created_at.desc()).limit(50).all()
        return render_template('nouvelle_conversation.html', users=users, current=user)

    @app.route('/conversation/<int:conv_id>', methods=['GET', 'POST'])
    @app.route('/conversation', methods=['GET', 'POST'])
    @login_required
    def conversation(conv_id=None):
        user = get_current_user()
        conv_id = conv_id or request.args.get('id', type=int)
        
        if conv_id:
            conv = Conversation.query.get_or_404(conv_id)
            # Securite: verifier que l'utilisateur fait partie de la conv
            if user.id not in [conv.user1_id, conv.user2_id]:
                abort(403)
            
            if request.method == 'POST':
                contenu = request.form.get('contenu', '').strip()
                if contenu:
                    msg = Message(conversation_id=conv.id, sender_id=user.id, contenu=contenu)
                    conv.last_message_at = datetime.utcnow()
                    db.session.add(msg)
                    db.session.commit()
                    return redirect(url_for('conversation', conv_id=conv.id))
            
            messages = conv.messages.order_by(Message.created_at.asc()).all()
            other_id = conv.user2_id if conv.user1_id == user.id else conv.user1_id
            other_user = User.query.get(other_id)
            return render_template('conversation.html', conversation=conv, messages=messages, other_user=other_user, user=user)
        
        return render_template('conversation.html', user=user)

    # --- PROFIL ---
    @app.route('/profil')
    @login_required
    def profil():
        user = get_current_user()
        my_posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
        followers_count = 0  # A implementer avec Follow
        return render_template('profil.html', user=user, posts=my_posts, stats={'posts': len(my_posts)})

    @app.route('/profil_public')
    @login_required
    def profil_public():
        current = get_current_user()
        user_id = request.args.get('id', type=int)
        user = User.query.get(user_id) if user_id else current
        if not user:
            abort(404)
        posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
        return render_template('profil_public.html', user=user, posts=posts, current_user=current)

    @app.route('/modifier_profil', methods=['GET', 'POST'])
    @login_required
    def modifier_profil():
        user = get_current_user()
        if request.method == 'POST':
            user.bio = request.form.get('bio', '')[:500]
            user.ville = request.form.get('ville', '')[:100]
            user.poste = request.form.get('poste', '')[:50]
            user.photo_url = request.form.get('photo_url', '')[:500]
            db.session.commit()
            flash('Profil mis a jour', 'success')
            return redirect(url_for('profil'))
        return render_template('modifier_profil.html', user=user)

    # --- AUTRES ---
    @app.route('/notifications')
    @login_required
    def notifications():
        user = get_current_user()
        notifs = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(50).all()
        return render_template('notifications.html', notifications=notifs, user=user)

    @app.route('/parametres', methods=['GET', 'POST'])
    @login_required
    def parametres():
        return render_template('parametres.html', user=get_current_user())

    @app.route('/langue')
    def langue():
        return render_template('langue.html')

    @app.route('/abonnement')
    @login_required
    def abonnement():
        return render_template('abonnement.html', user=get_current_user())

    @app.route('/acces_refuse')
    def acces_refuse():
        return render_template('acces_refuse.html')

    return app

# --- LANCEMENT ---
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)