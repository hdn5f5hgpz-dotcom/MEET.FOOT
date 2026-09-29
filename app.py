from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'meetfoot-secret-key-2026'

# Config uploads
UPLOAD_FOLDER = 'static/uploads'
AUDIO_FOLDER = 'static/audio'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3', 'wav', 'webm'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/inscription_club')
def inscription_club():
    return render_template('inscription_club.html')

@app.route('/inscription_particulier')
def inscription_particulier():
    return render_template('inscription_particulier.html')

@app.route('/accueil')
def accueil():
    return render_template('accueil.html')

@app.route('/creer')
def creer():
    return render_template('creer.html')

@app.route('/market')
def market():
    return render_template('market.html')

@app.route('/market_publier')
def market_publier():
    return render_template('market_publier.html')

@app.route('/messagerie')
def messagerie():
    return render_template('messagerie.html')

@app.route('/nouvelle_conversation')
def nouvelle_conversation():
    return render_template('nouvelle_conversation.html')

@app.route('/conversation')
def conversation():
    return render_template('conversation.html')

@app.route('/notifications')
def notifications():
    return render_template('notifications.html')

@app.route('/profil')
def profil():
    return render_template('profil.html')

@app.route('/profil_public')
def profil_public():
    return render_template('profil_public.html')

@app.route('/modifier_profil')
def modifier_profil():
    return render_template('modifier_profil.html')

@app.route('/parametres')
def parametres():
    return render_template('parametres.html')

@app.route('/langue')
def langue():
    return render_template('langue.html')

@app.route('/abonnement')
def abonnement():
    return render_template('abonnement.html')

@app.route('/acces_refuse')
def acces_refuse():
    return render_template('acces_refuse.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)