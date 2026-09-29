"""
app.py
------
C'est le fichier principal : celui qu'on lance pour démarrer le site.

Comment lancer l'appli :
    1. Ouvre un terminal dans ce dossier
    2. Installe Flask (une seule fois) :   pip install flask
    3.import base64
import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, session
import models

app = Flask(__name__)

DOSSIER_AUDIO = os.path.join("static", "audio")
os.makedirs(DOSSIER_AUDIO, exist_ok=True)
DOSSIER_MEDIA = os.path.join("static", "uploads")
os.makedirs(DOSSIER_MEDIA, exist_ok=True)

EXTENSIONS_IMAGE = {"png", "jpg", "jpeg", "gif", "webp"}
EXTENSIONS_VIDEO = {"mp4", "mov", "webm", "avi"}

def enregistrer_media(fichier):
    if fichier is None or fichier.filename == "":
        return None, None
    extension = fichier.filename.rsplit(".", 1)[-1].lower() if "." in fichier.filename else ""
    if extension in EXTENSIONS_IMAGE:
        type_media = "image"
    elif extension in EXTENSIONS_VIDEO:
        type_media = "video"
    else:
        return None, None
    nom_fichier = f"{uuid.uuid4().hex}.{extension}"
    fichier.save(os.path.join(DOSSIER_MEDIA, nom_fichier))
    return nom_fichier, type_media

def enregistrer_photo(fichier):
    nom_fichier, type_media = enregistrer_media(fichier)
    if type_media == "image":
        return nom_fichier
    return None

app.secret_key = "cle_secrete_a_changer_plus_tard"
models.init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/inscription/club", methods=["GET", "POST"])
def inscription_club():
    if request.method == "POST":
        models.creer_club(request.form["nom_club"], request.form.get("logo_url", ""), request.form["discipline"], request.form["pays"], request.form.get("ligue", ""), request.form["email"], request.form["mot_de_passe"])
        session["email"] = request.form["email"]
        session["type_compte"] = "club"
        return redirect(url_for("accueil"))
    return render_template("inscription_club.html")

@app.route("/inscription/particulier", methods=["GET", "POST"])
def inscription_particulier():
    if request.method == "POST":
        poste = request.form.get("poste", "") if request.form["profession"] == "Joueur" else ""
        models.creer_particulier(request.form["nom"], request.form["prenoms"], request.form["date_naissance"], request.form["nationalite"], request.form["profession"], request.form["sport"], poste, request.form["email"], request.form["mot_de_passe"])
        session["email"] = request.form["email"]
        session["type_compte"] = "particulier"
        return redirect(url_for("accueil"))
    return render_template("inscription_particulier.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    erreur = None
    if request.method == "POST":
        type_compte, utilisateur = models.trouver_utilisateur_par_email(request.form["email"])
        if utilisateur is not None and utilisateur["mot_de_passe"] == request.form["mot_de_passe"]:
            session["email"] = request.form["email"]
            session["type_compte"] = type_compte
            return redirect(url_for("accueil"))
        else:
            erreur = "Email ou mot de passe incorrect."
    return render_template("login.html", erreur=erreur)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

def utilisateur_connecte():
    return "email" in session

@app.context_processor
def injecter_notifications():
    if utilisateur_connecte():
        return {"nb_notifs_non_lues": models.compter_notifications_non_lues(session["email"]), "abonnement_ok": models.abonnement_est_actif(session["type_compte"], session["email"])}
    return {"nb_notifs_non_lues": 0, "abonnement_ok": False}

ENDPOINTS_SANS_ABONNEMENT = {"index", "inscription_club", "inscription_particulier", "login", "logout", "abonnement", "static"}

@app.before_request
def verifier_abonnement():
    if request.endpoint in ENDPOINTS_SANS_ABONNEMENT or request.endpoint is None:
        return None
    if not utilisateur_connecte():
        return None
    if not models.abonnement_est_actif(session["type_compte"], session["email"]):
        return redirect(url_for("abonnement"))
    return None

@app.route("/accueil", methods=["GET", "POST"])
def accueil():
    if not utilisateur_connecte():
        return redirect(url_for("login"))
    email = session["email"]
    type_compte = session["type_compte"]
    if request.method == "POST":
        contenu_texte = request.form.get("contenu_texte", "").strip()
        image_url = request.form.get("image_url", "").strip()
        if contenu_texte or image_url:
            _, utilisateur = models.trouver_utilisateur_par_email(email)
            auteur_nom = models.nom_affichage(type_compte, utilisateur)
            models.creer_post(type_compte, email, auteur_nom, contenu_texte, image_url)
        return redirect(url_for("accueil"))
    posts = models.lister_posts(email)
    return render_template("accueil.html", posts=posts, type_compte=type_compte)

@app.route("/like/<int:post_id>", methods=["POST"])
def like(post_id):
    if not utilisateur_connecte():
        return redirect(url_for("login"))
    email = session["email"]
    action = models.toggle_like(post_id, email)
    if action == "ajout":
        post = models.recuperer_post(post_id)
        if post is not None and post["auteur_email"]!= email:
            _, utilisateur = models.trouver_utilisateur_par_email(email)
            nom_utilisateur = models.nom_affichage(session["type_compte"], utilisateur)
            models.creer_notification(post["auteur_email"], "like", f"{nom_utilisateur} a aime votre publication.", url_for("accueil"))
    return redirect(url_for("accueil"))

@app.route("/notifications")
def notifications():
    if not utilisateur_connecte():
        return redirect(url_for("login"))
    liste = models.lister_notifications(session["email"])
    models.marquer_notifications_lues(session["email"])
    return render_template("notifications.html", notifications=liste)

@app.route("/creer", methods=["GET", "POST"])
def creer():
    if not utilisateur_connecte():
        return redirect(url_for("login"))
    if request.method == "POST":
        nom_fichier, type_media = enregistrer_media(request.files.get("media"))
        if request.form.get("contenu_texte", "").strip() or nom_fichier:
            _, utilisateur = models.trouver_utilisateur_par_email(session["email"])
            models.creer_post(session["type_compte"], session["email"], models.nom_affichage(session["type_compte"], utilisateur), request.form.get("contenu_texte", "").strip(), "", type_media, nom_fichier, request.form.get("visibilite", "public"))
        return redirect(url_for("accueil"))
    return render_template("creer.html")

@app.route("/messagerie")
def messagerie():
    if not utilisateur_connecte():
        return redirect(url_for("login"))
    return render_template("messagerie.html", conversations=models.lister_conversations(session["email"]))

@app.route("/messagerie/nouvelle")
def nouvelle_conversation():
    if not utilisateur_connecte():
        return redirect(url_for("login"))
    return render_template("nouvelle_conversation.html", contacts=models.lister_contacts_possibles(session["email"], session["type_compte"]))

@app.route("/messagerie/<autre_email>", methods=["GET", "POST"])
def conversation(autre_email):
    if not utilisateur_connecte():
        return redirect(url_for("login"))
    mon_email = session["email"]
    _, mon_compte = models.trouver_utilisateur_par_email(mon_email)
    mon_nom = models.nom_affichage(session["type_compte"], mon_compte)
    type_autre, autre_compte = models.trouver_utilisateur_par_email(autre_email)
    if autre_compte is None:
        return redirect(url_for("messagerie"))
    autre_nom = models.nom_affichage(type_autre, autre_compte)
    if request.method == "POST":
        contenu_texte = request.form.get("contenu_texte", "").strip()
        audio_base64 = request.form.get("audio_base64", "").strip()
        if contenu_texte:
            models.envoyer_message(mon_email, mon_nom, autre_email, autre_nom, "texte", contenu_texte)
        elif audio_base64:
            donnees_audio = base64.b64decode(audio_base64.split(",")[1])
            nom_fichier = f"{uuid.uuid4().hex}.webm"
            with open(os.path.join(DOSSIER_AUDIO, nom_fichier), "wb") as f:
                f.write(donnees_audio)
            models.envoyer_message(mon_email, mon_nom, autre_email, autre_nom, "vocal", nom_fichier)
        if contenu_texte or audio_base64:
            models.creer_notification(autre_email, "message", f"{mon_nom} vous a envoye un message.", url_for("conversation", autre_email=mon_email))
        return redirect(url_for("conversation", autre_email=autre_email))
    messages = models.lister_messages(mon_email, autre_email)
    return render_template("conversation.html", messages=messages, mon_email=mon_email, autre_email=autre_email, autre_nom=autre_nom)

@app.route("/market")
def market():
    if not utilisateur_connecte():
        return redirect(url_for("login"))
    _, compte = models.trouver_utilisateur_par_email(session["email"])
    return render_template("market.html", annonces=models.lister_annonces_market(), peut_publier=models.peut_publier_sur_market(session["type_compte"], compte))

@app.route("/market/publier", methods=["GET", "POST"])
def market_publier():
    if not utilisateur_connecte():
        return redirect(url_for("login"))
    email = session["email"]
    type_compte = session["type_compte"]
    _, compte = models.trouver_utilisateur_par_email(email)
    if not models.peut_publier_sur_market(type_compte, compte):
        return redirect(url_for("market"))
    if request.method == "POST":
        photo = enregistrer_photo(request.files.get("photo"))
        if type_compte == "club":
            models.creer_annonce_joueur(email, models.nom_affichage(type_compte, compte), compte["logo_url"], photo, request.form["nom_joueur"], request.form["poste"], request.form["age"], request.form.get("prix", "").strip())
        else:
            models.creer_annonce_recherche(email, models.nom_affichage(type_compte, compte), photo, request.form["texte_recherche"].strip())
        return redirect(url_for("market"))
    return render_template("market_publier.html", type_compte=type_compte)

@app.route("/profil")
def profil():
    if not utilisateur_connecte():
        return redirect(url_for("login"))
    _, compte = models.trouver_utilisateur_par_email(session["email"])
    return render_template("profil.html", compte=compte, type_compte=session["type_compte"], mes_posts=models.lister_posts_de(session["email"]))

@app.route("/profil/visite/<email_visite>")
def visiter_profil(email_visite):
    if not utilisateur_connecte():
        return redirect(url_for("login"))
    if email_visite == session["email"]:
        return redirect(url_for("profil"))
    type_du_visite, compte_visite = models.trouver_utilisateur_par_email(email_visite)
    if compte_visite is None:
        return redirect(url_for("accueil"))
    if not models.peut_visiter(session["type_compte"], type_du_visite):
        return render_template("acces_refuse.html", nom=models.nom_affichage(type_du_visite, compte_visite))
    return render_template("profil_public.html", compte=compte_visite, type_compte=type_du_visite, email_visite=email_visite, posts=models.lister_posts_publics_de(email_visite))

@app.route("/profil/post/<int:post_id>/visibilite", methods=["POST"])
def basculer_visibilite_post(post_id):
    if not utilisateur_connecte():
        return redirect(url_for("login"))
    models.changer_visibilite_post(post_id, session["email"])
    return redirect(url_for("profil"))

@app.route("/profil/parametres")
def parametres():
    if not utilisateur_connecte():
        return redirect(url_for("login"))
    return render_template("parametres.html")

@app.route("/profil/modifier", methods=["GET", "POST"])
def modifier_profil():
    if not utilisateur_connecte():
        return redirect(url_for("login"))
    email = session["email"]
    type_compte = session["type_compte"]
    _, compte = models.trouver_utilisateur_par_email(email)
    if request.method == "POST":
        if type_compte == "club":
            models.modifier_club(email, request.form["nom_club"], request.form.get("logo_url", ""), request.form["pays"], request.form.get("ligue", ""))
        else:
            models.modifier_particulier(email, request.form["nom"], request.form["prenoms"], request.form["nationalite"], request.form.get("poste", ""))
        return redirect(url_for("profil"))
    return render_template("modifier_profil.html", compte=compte, type_compte=type_compte)

@app.route("/profil/langue", methods=["GET", "POST"])
def langue():
    if not utilisateur_connecte():
        return redirect(url_for("login"))
    if request.method == "POST":
        models.changer_langue(session["type_compte"], session["email"], request.form["langue"])
        return redirect(url_for("parametres"))
    _, compte = models.trouver_utilisateur_par_email(session["email"])
    return render_template("langue.html", langue_actuelle=compte["langue"])

@app.route("/profil/abonnement", methods=["GET", "POST"])
def abonnement():
    if not utilisateur_connecte():
        return redirect(url_for("login"))
    email = session["email"]
    type_compte = session["type_compte"]
    if request.method == "POST":
        if request.form.get("action") == "resilier":
            models.resilier_abonnement(type_compte, email)
        else:
            moyen = request.form.get("moyen_paiement")
            if moyen in models.MOYENS_DE_PAIEMENT:
                models.activer_abonnement(type_compte, email, moyen)
        return redirect(url_for("abonnement"))
    _, compte = models.trouver_utilisateur_par_email(email)
    return render_template("abonnement.html", actif=models.abonnement_est_actif(type_compte, email), prix=models.prix_abonnement(type_compte), moyens=models.MOYENS_DE_PAIEMENT, moyen_actuel=compte["moyen_paiement"])

if __name__ == "__main__":
    app.run(debug=True)- une vraie traduction de l'interface selon la langue choisie
- brancher un vrai fournisseur de paiement mobile money
- déployer l'appli en ligne pour que d'autres puissent la tester
