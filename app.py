from flask import Flask, render_template, request, redirect, url_for, session, flash
import os

app = Flask(__name__)
app.secret_key = 'meetfoot-secret-key-2026'

os.makedirs('static/uploads', exist_ok=True)
os.makedirs('static/audio', exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return redirect(url_for('accueil'))
    return render_template('login.html')

@app.route('/inscription_club', methods=['GET', 'POST'])
def inscription_club():
    if request.method == 'POST':
        return redirect(url_for('accueil'))
    return render_template('inscription_club.html')

@app.route('/inscription_particulier', methods=['GET', 'POST'])
def inscription_particulier():
    if request.method == 'POST':
        return redirect(url_for('accueil'))
    return render_template('inscription_particulier.html')

@app.route('/accueil', methods=['GET', 'POST'])
def accueil():
    return render_template('accueil.html')

@app.route('/creer', methods=['GET', 'POST'])
def creer():
    return render_template('creer.html')

@app.route('/market', methods=['GET', 'POST'])
def market():
    return render_template('market.html')

@app.route('/market_publier', methods=['GET', 'POST'])
def market_publier():
    return render_template('market_publier.html')

@app.route('/messagerie', methods=['GET', 'POST'])
def messagerie():
    return render_template('messagerie.html')

@app.route('/nouvelle_conversation', methods=['GET', 'POST'])
def nouvelle_conversation():
    return render_template('nouvelle_conversation.html')

@app.route('/conversation', methods=['GET', 'POST'])
def conversation():
    return render_template('conversation.html')

@app.route('/notifications', methods=['GET', 'POST'])
def notifications():
    return render_template('notifications.html')

@app.route('/profil', methods=['GET', 'POST'])
def profil():
    return render_template('profil.html')

@app.route('/profil_public', methods=['GET', 'POST'])
def profil_public():
    return render_template('profil_public.html')

@app.route('/modifier_profil', methods=['GET', 'POST'])
def modifier_profil():
    return render_template('modifier_profil.html')

@app.route('/parametres', methods=['GET', 'POST'])
def parametres():
    return render_template('parametres.html')

@app.route('/langue', methods=['GET', 'POST'])
def langue():
    return render_template('langue.html')

@app.route('/abonnement', methods=['GET', 'POST'])
def abonnement():
    return render_template('abonnement.html')

@app.route('/acces_refuse', methods=['GET', 'POST'])
def acces_refuse():
    return render_template('acces_refuse.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)