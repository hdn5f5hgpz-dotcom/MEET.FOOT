"""
app.py
------
C'est le fichier principal : celui qu'on lance pour démarrer le site.

Comment lancer l'appli :
    1. Ouvre un terminal dans ce dossier
    2. Installe Flask (une seule fois) :   pip install flask
    3. Lance le serveur :                  python app.py
    4. Ouvre ton navigateur à l'adresse :  http://127.0.0.1:5000

Vocabulaire utile :
- une "route" (@app.route) associe une adresse web (ex: "/login")
  à une fonction Python qui décide quoi afficher.
- `request` contient les infos envoyées par le navigateur (ex: le contenu
  d'un formulaire rempli par l'utilisateur).
- `session` permet de "se souvenir" qu'un utilisateur est connecté,
  entre deux pages.
"""

import base64
import os
import uuid

from flask import Flask, render_template, request, redirect, url_for, session
import models

app = Flask(__name__)

# Dossier où seront enregistrés les messages vocaux (fichiers audio).
DOSSIER_AUDIO = os.path.join("static", "audio")
os.makedirs(DOSSIER_AUDIO, exist_ok=True)

# Dossier où seront enregistrées les photos/vidéos (onglet Créer et Market).
DOSSIER_MEDIA = os.path.join("static", "uploads")
os.makedirs(DOSSIER_MEDIA, exist_ok=True)

EXTENSIONS_IMAGE = {"png", "jpg", "jpeg", "gif", "webp"}
EXTENSIONS_VIDEO = {"mp4", "mov", "webm", "avi"}


def enregistrer_media(fichier):
    """
    Sauve un fichier uploadé (photo OU vidéo) avec un nom unique pour ne
    jamais écraser un fichier existant.
    Renvoie (nom_fichier, type_media) ou (None, None) si rien d'utilisable
    n'a été envoyé (champ vide, ou extension non reconnue).
    """
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
    """Comme enregistrer_media, mais n'accepte que les images (utilisé par le Market)."""
    nom_fichier, type_media = enregistrer_media(fichier)
    if type_media == "image":
        return nom_fichier
    return None

# La "secret_key" sert à sécuriser les sessions (connexions) des utilisateurs.
# Pour un vrai projet en ligne, il faudra une clé longue et secrète.
app.secret_key = "cle_secrete_a_changer_plus_tard"

# On crée les tables de la base de données au démarrage (si elles n'existent pas).
models.init_db()


# ---------------------------------------------------------------------------
# PAGE D'ACCUEIL DU SITE (avant connexion) : choix Club / Particulier / Login
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# INSCRIPTION : COMPTE CLUB
# ---------------------------------------------------------------------------
@app.route("/inscription/club", methods=["GET", "POST"])
def inscription_club():
    # GET = l'utilisateur arrive juste sur la page (on affiche le formulaire)
    # POST = l'utilisateur a rempli et envoyé le formulaire
    if request.method == "POST":
        nom_club = request.form["nom_club"]
        logo_url = request.form.get("logo_url", "")
        discipline = request.form["discipline"]
        pays = request.form["pays"]
        ligue = request.form.get("ligue", "")
        email = request.form["email"]
        mot_de_passe = request.form["mot_de_passe"]

        models.creer_club(nom_club, logo_url, discipline, pays, ligue, email, mot_de_passe)

        # On connecte directement le club après son inscription.
        session["email"] = email
        session["type_compte"] = "club"
        return redirect(url_for("accueil"))

    return render_template("inscription_club.html")


# ---------------------------------------------------------------------------
# INSCRIPTION : COMPTE PARTICULIER
# ---------------------------------------------------------------------------
@app.route("/inscription/particulier", methods=["GET", "POST"])
def inscription_particulier():
    if request.method == "POST":
        nom = request.form["nom"]
        prenoms = request.form["prenoms"]
        date_naissance = request.form["date_naissance"]
        nationalite = request.form["nationalite"]
        profession = request.form["profession"]
        sport = request.form["sport"]
        # Le poste sur le terrain ne concerne que les joueurs.
        poste = request.form.get("poste", "") if profession == "Joueur" else ""
        email = request.form["email"]
        mot_de_passe = request.form["mot_de_passe"]

        models.creer_particulier(nom, prenoms, date_naissance, nationalite,
                                  profession, sport, poste, email, mot_de_passe)

        session["email"] = email
        session["type_compte"] = "particulier"
        return redirect(url_for("accueil"))

    return render_template("inscription_particulier.html")


# ---------------------------------------------------------------------------
# CONNEXION
# ---------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    erreur = None
    if request.method == "POST":
        email = request.form["email"]
        mot_de_passe = request.form["mot_de_passe"]

        type_compte, utilisateur = models.trouver_utilisateur_par_email(email)

        if utilisateur is not None and utilisateur["mot_de_passe"] == mot_de_passe:
            session["email"] = email
            session["type_compte"] = type_compte
            return redirect(url_for("accueil"))
        else:
            erreur = "Email ou mot de passe incorrect."

    return render_template("login.html", erreur=erreur)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Petite fonction utilitaire : vérifie qu'un utilisateur est connecté
# avant de lui montrer une page réservée aux membres.
# ---------------------------------------------------------------------------
def utilisateur_connecte():
    return "email" in session


# Un "context_processor" s'exécute automatiquement avant CHAQUE page.
# Ici, il ajoute la variable "nb_notifs_non_lues" à tous les templates,
# pour afficher la petite pastille sur l'icône 🔔 sans le répéter dans
# chaque route.
@app.context_processor
def injecter_notifications():
    if utilisateur_connecte():
        type_compte = session["type_compte"]
        email = session["email"]
        return {
            "nb_notifs_non_lues": models.compter_notifications_non_lues(email),
            "abonnement_ok": models.abonnement_est_actif(type_compte, email),
        }
    return {"nb_notifs_non_lues": 0, "abonnement_ok": False}


# ---------------------------------------------------------------------------
# ABONNEMENT OBLIGATOIRE
# L'application est payante : tant qu'un compte n'a pas payé son abonnement
# mensuel, il ne peut accéder à AUCUN onglet. Ces quelques pages restent
# accessibles sans être abonné (inscription, connexion, page de paiement
# elle-même, et les fichiers statiques comme les photos/vidéos/audios).
# ---------------------------------------------------------------------------
ENDPOINTS_SANS_ABONNEMENT = {
    "index", "inscription_club", "inscription_particulier",
    "login", "logout", "abonnement", "static",
}


@app.before_request
def verifier_abonnement():
    # "before_request" s'exécute AVANT chaque route, sur tout le site.
    if request.endpoint in ENDPOINTS_SANS_ABONNEMENT or request.endpoint is None:
        return None  # rien à vérifier, on laisse passer

    if not utilisateur_connecte():
        return None  # la route elle-même redirigera vers /login

    type_compte = session["type_compte"]
    email = session["email"]
    if not models.abonnement_est_actif(type_compte, email):
        return redirect(url_for("abonnement"))

    return None


# ---------------------------------------------------------------------------
# LES 6 ONGLETS PRINCIPAUX (accessibles une fois connecté)
# Pour l'instant ce sont des pages simples "à construire" : on les
# détaillera un par un dans les prochaines étapes.
# ---------------------------------------------------------------------------
@app.route("/accueil", methods=["GET", "POST"])
def accueil():
    if not utilisateur_connecte():
        return redirect(url_for("login"))

    email = session["email"]
    type_compte = session["type_compte"]

    # Si l'utilisateur envoie le petit formulaire de publication en haut
    # du fil d'actualité, on enregistre le post avant de réafficher la page.
    if request.method == "POST":
        contenu_texte = request.form.get("contenu_texte", "").strip()
        image_url = request.form.get("image_url", "").strip()

        # On ne publie que si l'utilisateur a écrit au moins un texte ou une image.
        if contenu_texte or image_url:
            _, utilisateur = models.trouver_utilisateur_par_email(email)
            auteur_nom = models.nom_affichage(type_compte, utilisateur)
            models.creer_post(type_compte, email, auteur_nom, contenu_texte, image_url)

        # On redirige (plutôt que d'afficher directement) pour éviter
        # qu'un rafraîchissement de la page ne republie le même post.
        return redirect(url_for("accueil"))

    posts = models.lister_posts(email)
    return render_template("accueil.html", posts=posts, type_compte=type_compte)


@app.route("/like/<int:post_id>", methods=["POST"])
def like(post_id):
    if not utilisateur_connecte():
        return redirect(url_for("login"))

    email = session["email"]
    action = models.toggle_like(post_id, email)

    # On ne notifie l'auteur du post QUE si :
    # - c'est un nouveau like (pas un "unlike")
    # - il ne s'est pas liké lui-même
    if action == "ajout":
        post = models.recuperer_post(post_id)
        if post is not None and post["auteur_email"] != email:
            _, utilisateur = models.trouver_utilisateur_par_email(email)
            nom_utilisateur = models.nom_affichage(session["type_compte"], utilisateur)
            models.creer_notification(
                destinataire_email=post["auteur_email"],
                type_notification="like",
                texte=f"{nom_utilisateur} a aimé votre publication.",
                lien=url_for("accueil"),
            )

    return redirect(url_for("accueil"))


@app.route("/notifications")
def notifications():
    if not utilisateur_connecte():
        return redirect(url_for("login"))

    email = session["email"]
    liste = models.lister_notifications(email)

    # On marque tout comme "lu" une fois que l'utilisateur a ouvert la page
    # (comme sur Facebook : la pastille rouge disparaît après consultation).
    models.marquer_notifications_lues(email)

    return render_template("notifications.html", notifications=liste)


@app.route("/creer", methods=["GET", "POST"])
def creer():
    if not utilisateur_connecte():
        return redirect(url_for("login"))

    if request.method == "POST":
        email = session["email"]
        type_compte = session["type_compte"]
        contenu_texte = request.form.get("contenu_texte", "").strip()
        visibilite = request.form.get("visibilite", "public")
        fichier = request.files.get("media")

        nom_fichier, type_media = enregistrer_media(fichier)

        # On ne publie que s'il y a au moins un texte OU un média.
        if contenu_texte or nom_fichier:
            _, utilisateur = models.trouver_utilisateur_par_email(email)
            auteur_nom = models.nom_affichage(type_compte, utilisateur)
            models.creer_post(type_compte, email, auteur_nom, contenu_texte, image_url="",
                               type_media=type_media, fichier_media=nom_fichier, visibilite=visibilite)

        return redirect(url_for("accueil"))

    return render_template("creer.html")


@app.route("/messagerie")
def messagerie():
    if not utilisateur_connecte():
        return redirect(url_for("login"))
    conversations = models.lister_conversations(session["email"])
    return render_template("messagerie.html", conversations=conversations)


@app.route("/messagerie/nouvelle")
def nouvelle_conversation():
    if not utilisateur_connecte():
        return redirect(url_for("login"))
    contacts = models.lister_contacts_possibles(session["email"], session["type_compte"])
    return render_template("nouvelle_conversation.html", contacts=contacts)


@app.route("/messagerie/<autre_email>", methods=["GET", "POST"])
def conversation(autre_email):
    if not utilisateur_connecte():
        return redirect(url_for("login"))

    mon_email = session["email"]
    mon_type = session["type_compte"]

    _, mon_compte = models.trouver_utilisateur_par_email(mon_email)
    mon_nom = models.nom_affichage(mon_type, mon_compte)

    type_autre, autre_compte = models.trouver_utilisateur_par_email(autre_email)
    if autre_compte is None:
        # Ce contact n'existe pas (mauvais lien, compte supprimé...).
        return redirect(url_for("messagerie"))
    autre_nom = models.nom_affichage(type_autre, autre_compte)

    if request.method == "POST":
        contenu_texte = request.form.get("contenu_texte", "").strip()
        audio_base64 = request.form.get("audio_base64", "").strip()

        if contenu_texte:
            models.envoyer_message(mon_email, mon_nom, autre_email, autre_nom, "texte", contenu_texte)

        elif audio_base64:
            # audio_base64 ressemble à "data:audio/webm;base64,XXXXXX" :
            # on ne garde que la partie après la virgule pour la décoder.
            donnees_audio = base64.b64decode(audio_base64.split(",")[1])
            nom_fichier = f"{uuid.uuid4().hex}.webm"
            with open(os.path.join(DOSSIER_AUDIO, nom_fichier), "wb") as fichier:
                fichier.write(donnees_audio)
            models.envoyer_message(mon_email, mon_nom, autre_email, autre_nom, "vocal", nom_fichier)

        if contenu_texte or audio_base64:
            models.creer_notification(
                destinataire_email=autre_email,
                type_notification="message",
                texte=f"{mon_nom} vous a envoyé un message.",
                lien=url_for("conversation", autre_email=mon_email),
            )

        return redirect(url_for("conversation", autre_email=autre_email))

    messages = models.lister_messages(mon_email, autre_email)
    return render_template("conversation.html", messages=messages, mon_email=mon_email,
                            autre_email=autre_email, autre_nom=autre_nom)


@app.route("/market")
def market():
    if not utilisateur_connecte():
        return redirect(url_for("login"))

    _, compte = models.trouver_utilisateur_par_email(session["email"])
    # Rappel du cahier des charges : seuls Clubs, Agents et Coachs peuvent
    # POSTER sur le Market. Les Joueurs peuvent seulement le consulter.
    peut_publier = models.peut_publier_sur_market(session["type_compte"], compte)
    annonces = models.lister_annonces_market()
    return render_template("market.html", annonces=annonces, peut_publier=peut_publier)


@app.route("/market/publier", methods=["GET", "POST"])
def market_publier():
    if not utilisateur_connecte():
        return redirect(url_for("login"))

    email = session["email"]
    type_compte = session["type_compte"]
    _, compte = models.trouver_utilisateur_par_email(email)

    # Sécurité : même si le lien n'est pas affiché à un Joueur, on bloque
    # aussi la route elle-même pour qu'il ne puisse pas publier en tapant
    # l'adresse directement.
    if not models.peut_publier_sur_market(type_compte, compte):
        return redirect(url_for("market"))

    auteur_nom = models.nom_affichage(type_compte, compte)

    if request.method == "POST":
        photo = enregistrer_photo(request.files.get("photo"))

        if type_compte == "club":
            nom_joueur = request.form["nom_joueur"]
            poste = request.form["poste"]
            age = request.form["age"]
            prix = request.form.get("prix", "").strip()
            models.creer_annonce_joueur(email, auteur_nom, compte["logo_url"], photo,
                                         nom_joueur, poste, age, prix)
        else:
            texte_recherche = request.form["texte_recherche"].strip()
            models.creer_annonce_recherche(email, auteur_nom, photo, texte_recherche)

        return redirect(url_for("market"))

    return render_template("market_publier.html", type_compte=type_compte)


@app.route("/profil")
def profil():
    if not utilisateur_connecte():
        return redirect(url_for("login"))

    email = session["email"]
    type_compte = session["type_compte"]
    _, compte = models.trouver_utilisateur_par_email(email)
    mes_posts = models.lister_posts_de(email)

    return render_template("profil.html", compte=compte, type_compte=type_compte, mes_posts=mes_posts)


@app.route("/profil/visite/<email_visite>")
def visiter_profil(email_visite):
    if not utilisateur_connecte():
        return redirect(url_for("login"))

    # Si on "visite" son propre profil, on renvoie vers la vraie page Profil
    # (avec les options de modification, les posts privés, etc.)
    if email_visite == session["email"]:
        return redirect(url_for("profil"))

    type_du_visite, compte_visite = models.trouver_utilisateur_par_email(email_visite)
    if compte_visite is None:
        return redirect(url_for("accueil"))

    # Règle du cahier des charges : un Particulier ne peut visiter que les
    # Comptes Club, pas un autre Compte particulier. Un Club peut visiter
    # tout le monde.
    if not models.peut_visiter(session["type_compte"], type_du_visite):
        return render_template("acces_refuse.html", nom=models.nom_affichage(type_du_visite, compte_visite))

    posts_publics = models.lister_posts_publics_de(email_visite)
    return render_template("profil_public.html", compte=compte_visite, type_compte=type_du_visite,
                            email_visite=email_visite, posts=posts_publics)


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
            models.modifier_club(
                email,
                request.form["nom_club"],
                request.form.get("logo_url", ""),
                request.form["pays"],
                request.form.get("ligue", ""),
            )
        else:
            models.modifier_particulier(
                email,
                request.form["nom"],
                request.form["prenoms"],
                request.form["nationalite"],
                request.form.get("poste", ""),
            )
        return redirect(url_for("profil"))

    return render_template("modifier_profil.html", compte=compte, type_compte=type_compte)


@app.route("/profil/langue", methods=["GET", "POST"])
def langue():
    if not utilisateur_connecte():
        return redirect(url_for("login"))

    email = session["email"]
    type_compte = session["type_compte"]

    if request.method == "POST":
        models.changer_langue(type_compte, email, request.form["langue"])
        return redirect(url_for("parametres"))

    _, compte = models.trouver_utilisateur_par_email(email)
    return render_template("langue.html", langue_actuelle=compte["langue"])


@app.route("/profil/abonnement", methods=["GET", "POST"])
def abonnement():
    if not utilisateur_connecte():
        return redirect(url_for("login"))

    email = session["email"]
    type_compte = session["type_compte"]

    if request.method == "POST":
        action = request.form.get("action")
        if action == "resilier":
            models.resilier_abonnement(type_compte, email)
        else:
            moyen_paiement = request.form.get("moyen_paiement")
            # Sécurité simple : on vérifie que le moyen choisi fait bien
            # partie de la liste autorisée (Wave / Moov Money / MTN Money).
            if moyen_paiement in models.MOYENS_DE_PAIEMENT:
                models.activer_abonnement(type_compte, email, moyen_paiement)
        return redirect(url_for("abonnement"))

    _, compte = models.trouver_utilisateur_par_email(email)
    return render_template(
        "abonnement.html",
        actif=models.abonnement_est_actif(type_compte, email),
        prix=models.prix_abonnement(type_compte),
        moyens=models.MOYENS_DE_PAIEMENT,
        moyen_actuel=compte["moyen_paiement"],
    )


# ---------------------------------------------------------------------------
# Ce bloc ne s'exécute que si on lance directement "python app.py"
# (et pas si ce fichier est importé ailleurs). debug=True affiche les
# erreurs détaillées dans le navigateur, pratique pour apprendre.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
"""
models.py
---------
Ce fichier gère la base de données (ici SQLite, un fichier local, parfait
pour débuter : pas besoin d'installer de serveur de base de données).

On y stocke deux "tables" :
- clubs         : les comptes "Compte Club"
- particuliers   : les comptes "Compte particulier" (agents, coachs, joueurs)

Rappel de vocabulaire Python utilisé ici :
- une fonction est définie avec le mot-clé `def`
- `self` désigne "l'objet lui-même" dans une classe (on l'explique plus bas)
- `#` démarre un commentaire, ignoré par Python
"""

import sqlite3

# Nom du fichier qui contiendra toute la base de données de l'appli.
DB_NAME = "meet_foot.db"


def get_connection():
    """
    Ouvre une connexion vers le fichier de base de données.
    On appelle cette fonction à chaque fois qu'on veut lire ou écrire
    des données.
    """
    connection = sqlite3.connect(DB_NAME)
    # Cette ligne permet de récupérer les résultats sous forme de
    # dictionnaires (colonne -> valeur) plutôt que de simples listes.
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """
    Crée les tables si elles n'existent pas encore.
    À appeler une seule fois, au démarrage de l'appli.
    """
    connection = get_connection()
    cursor = connection.cursor()

    # Table des comptes "Club"
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clubs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_club TEXT NOT NULL,
            logo_url TEXT,
            discipline TEXT NOT NULL,     -- Football / Handball / Basketball
            pays TEXT NOT NULL,
            ligue TEXT,
            email TEXT UNIQUE NOT NULL,
            mot_de_passe TEXT NOT NULL
        )
    """)

    # Table des comptes "Particulier"
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS particuliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenoms TEXT NOT NULL,
            date_naissance TEXT NOT NULL,
            nationalite TEXT NOT NULL,
            profession TEXT NOT NULL,     -- Agent / Coach / Joueur
            sport TEXT NOT NULL,          -- Football / Handball / Basketball
            poste TEXT,                   -- uniquement rempli si Joueur
            email TEXT UNIQUE NOT NULL,
            mot_de_passe TEXT NOT NULL
        )
    """)

    # Table des publications (posts) affichées dans l'onglet Accueil.
    # auteur_type + auteur_email permettent de savoir QUI a posté, sans
    # dupliquer toutes les infos du compte à chaque fois.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            auteur_type TEXT NOT NULL,     -- "club" ou "particulier"
            auteur_email TEXT NOT NULL,
            auteur_nom TEXT NOT NULL,      -- nom déjà "prêt à afficher"
            contenu_texte TEXT,
            image_url TEXT,
            date_publication TEXT NOT NULL
        )
    """)

    # Table des likes : une ligne = "cet email a liké ce post".
    # UNIQUE(post_id, email_utilisateur) empêche de liker 2 fois le même post.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            email_utilisateur TEXT NOT NULL,
            UNIQUE(post_id, email_utilisateur)
        )
    """)

    # Table des messages échangés dans la Messagerie (texte OU vocal, illimité).
    # type_message = "texte"  -> contenu contient le texte écrit
    # type_message = "vocal"  -> contenu contient le NOM du fichier audio
    #                            (le fichier lui-même est dans static/audio/)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expediteur_email TEXT NOT NULL,
            expediteur_nom TEXT NOT NULL,
            destinataire_email TEXT NOT NULL,
            destinataire_nom TEXT NOT NULL,
            type_message TEXT NOT NULL,      -- "texte" ou "vocal"
            contenu TEXT NOT NULL,
            date_envoi TEXT NOT NULL
        )
    """)

    # Table des notifications (façon Facebook) : un like reçu ou un
    # message reçu en génère une. "lue" vaut 0 (non lue) ou 1 (lue).
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destinataire_email TEXT NOT NULL,
            type_notification TEXT NOT NULL,  -- "like" ou "message"
            texte TEXT NOT NULL,
            lien TEXT NOT NULL,
            date_notification TEXT NOT NULL,
            lue INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Table des annonces du Market.
    # categorie = "joueur"    -> un Club met un joueur en vente
    # categorie = "recherche" -> un Agent ou un Coach signale ce qu'il recherche
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            auteur_email TEXT NOT NULL,
            auteur_nom TEXT NOT NULL,       -- nom du club, ou de l'agent/coach
            logo_url TEXT,                  -- logo du club (catégorie "joueur")
            categorie TEXT NOT NULL,        -- "joueur" ou "recherche"
            photo TEXT,                     -- photo du joueur, ou de l'agent/coach
            nom_affiche TEXT NOT NULL,      -- nom du joueur, ou de l'agent/coach
            description TEXT,               -- "poste • âge" (joueur) ou texte libre (recherche)
            prix TEXT,                      -- uniquement pour un joueur, facultatif
            date_publication TEXT NOT NULL
        )
    """)

    # "commit" enregistre définitivement les changements dans le fichier.
    connection.commit()
    connection.close()

    # --- Petites "migrations" -----------------------------------------
    # Si l'appli existait déjà avant l'ajout de l'onglet Créer/Profil,
    # ces colonnes n'existent pas encore dans le fichier meet_foot.db.
    # ALTER TABLE les ajoute sans effacer les données déjà présentes.
    # On ignore l'erreur si la colonne existe déjà (cas d'une base neuve).
    ajouter_colonne_si_absente("posts", "type_media", "TEXT")       # "image" ou "video"
    ajouter_colonne_si_absente("posts", "fichier_media", "TEXT")    # nom du fichier uploadé
    ajouter_colonne_si_absente("posts", "visibilite", "TEXT NOT NULL DEFAULT 'public'")
    ajouter_colonne_si_absente("clubs", "premium", "INTEGER NOT NULL DEFAULT 0")
    ajouter_colonne_si_absente("clubs", "langue", "TEXT NOT NULL DEFAULT 'Français'")
    ajouter_colonne_si_absente("particuliers", "premium", "INTEGER NOT NULL DEFAULT 0")
    ajouter_colonne_si_absente("particuliers", "langue", "TEXT NOT NULL DEFAULT 'Français'")
    # L'application est payante (cf. cahier des charges) : chaque compte doit
    # avoir un abonnement actif pour utiliser l'appli, réglé en Wave / Moov
    # Money / MTN Money. abonnement_actif vaut 0 (pas payé) ou 1 (à jour).
    ajouter_colonne_si_absente("clubs", "abonnement_actif", "INTEGER NOT NULL DEFAULT 0")
    ajouter_colonne_si_absente("clubs", "moyen_paiement", "TEXT")
    ajouter_colonne_si_absente("particuliers", "abonnement_actif", "INTEGER NOT NULL DEFAULT 0")
    ajouter_colonne_si_absente("particuliers", "moyen_paiement", "TEXT")


def ajouter_colonne_si_absente(table, colonne, type_sql):
    """
    Ajoute une colonne à une table existante si elle n'y est pas déjà.
    Pratique pour faire évoluer la base de données sans perdre les
    comptes déjà créés lors des étapes précédentes.
    """
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {colonne} {type_sql}")
        connection.commit()
    except sqlite3.OperationalError:
        # La colonne existe déjà : rien à faire.
        pass
    connection.close()


def creer_club(nom_club, logo_url, discipline, pays, ligue, email, mot_de_passe):
    """Ajoute un nouveau compte Club dans la base de données."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO clubs (nom_club, logo_url, discipline, pays, ligue, email, mot_de_passe)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (nom_club, logo_url, discipline, pays, ligue, email, mot_de_passe))
    connection.commit()
    connection.close()


def creer_particulier(nom, prenoms, date_naissance, nationalite, profession,
                       sport, poste, email, mot_de_passe):
    """Ajoute un nouveau compte Particulier dans la base de données."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO particuliers
            (nom, prenoms, date_naissance, nationalite, profession, sport, poste, email, mot_de_passe)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (nom, prenoms, date_naissance, nationalite, profession, sport, poste, email, mot_de_passe))
    connection.commit()
    connection.close()


def trouver_utilisateur_par_email(email):
    """
    Cherche un compte (club OU particulier) à partir de son email.
    Renvoie un tuple (type_de_compte, données) ou (None, None) si rien trouvé.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM clubs WHERE email = ?", (email,))
    club = cursor.fetchone()
    if club is not None:
        connection.close()
        return "club", club

    cursor.execute("SELECT * FROM particuliers WHERE email = ?", (email,))
    particulier = cursor.fetchone()
    connection.close()
    if particulier is not None:
        return "particulier", particulier

    return None, None


def nom_affichage(type_compte, utilisateur):
    """
    Construit le nom à afficher publiquement selon le type de compte :
    - un club affiche son nom_club
    - un particulier affiche "Prénoms Nom"
    """
    if type_compte == "club":
        return utilisateur["nom_club"]
    else:
        return f"{utilisateur['prenoms']} {utilisateur['nom']}"


def creer_post(auteur_type, auteur_email, auteur_nom, contenu_texte, image_url,
                type_media=None, fichier_media=None, visibilite="public"):
    """
    Enregistre une nouvelle publication dans le fil d'actualité.
    - image_url : lien externe vers une image (utilisé par le mini-formulaire
      de l'onglet Accueil)
    - type_media / fichier_media : "image" ou "video" + nom du fichier
      uploadé (utilisé par l'onglet Créer, façon TikTok)
    """
    from datetime import datetime
    connection = get_connection()
    cursor = connection.cursor()
    date_publication = datetime.now().strftime("%d/%m/%Y %H:%M")
    cursor.execute("""
        INSERT INTO posts (auteur_type, auteur_email, auteur_nom, contenu_texte, image_url,
                            type_media, fichier_media, visibilite, date_publication)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (auteur_type, auteur_email, auteur_nom, contenu_texte, image_url,
          type_media, fichier_media, visibilite, date_publication))
    connection.commit()
    connection.close()


def lister_posts(email_utilisateur_courant):
    """
    Renvoie les posts visibles par l'utilisateur courant (les posts publics
    de tout le monde + ses propres posts privés), du plus récent au plus
    ancien, avec le nombre de likes et si l'utilisateur courant a déjà liké.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM posts
        WHERE visibilite = 'public' OR auteur_email = ?
        ORDER BY id DESC
    """, (email_utilisateur_courant,))
    posts_bruts = cursor.fetchall()

    posts = []
    for post in posts_bruts:
        cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id = ?", (post["id"],))
        nombre_likes = cursor.fetchone()[0]

        cursor.execute(
            "SELECT 1 FROM likes WHERE post_id = ? AND email_utilisateur = ?",
            (post["id"], email_utilisateur_courant)
        )
        deja_like = cursor.fetchone() is not None

        # On transforme la ligne en dictionnaire simple pour pouvoir y
        # ajouter facilement "nombre_likes" et "deja_like".
        post_dict = dict(post)
        post_dict["nombre_likes"] = nombre_likes
        post_dict["deja_like"] = deja_like
        posts.append(post_dict)

    connection.close()
    return posts


def recuperer_post(post_id):
    """Renvoie les infos d'un post à partir de son id (utile pour savoir
    qui en est l'auteur, par exemple pour notifier quand il reçoit un like)."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    connection.close()
    return post


def toggle_like(post_id, email_utilisateur):
    """
    Ajoute un like si l'utilisateur n'avait pas encore liké ce post,
    ou le retire s'il avait déjà liké (comme sur Instagram : on reclique
    pour annuler).
    Renvoie "ajout" ou "suppression" pour savoir quoi faire ensuite
    (par exemple : n'envoyer une notification qu'en cas d'ajout).
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id FROM likes WHERE post_id = ? AND email_utilisateur = ?",
        (post_id, email_utilisateur)
    )
    like_existant = cursor.fetchone()

    if like_existant is not None:
        cursor.execute("DELETE FROM likes WHERE id = ?", (like_existant["id"],))
        action = "suppression"
    else:
        cursor.execute(
            "INSERT INTO likes (post_id, email_utilisateur) VALUES (?, ?)",
            (post_id, email_utilisateur)
        )
        action = "ajout"

    connection.commit()
    connection.close()
    return action


# ---------------------------------------------------------------------------
# MESSAGERIE
# ---------------------------------------------------------------------------
def envoyer_message(expediteur_email, expediteur_nom, destinataire_email,
                     destinataire_nom, type_message, contenu):
    """Enregistre un message (texte ou vocal) entre deux utilisateurs."""
    from datetime import datetime
    connection = get_connection()
    cursor = connection.cursor()
    date_envoi = datetime.now().strftime("%d/%m/%Y %H:%M")
    cursor.execute("""
        INSERT INTO messages
            (expediteur_email, expediteur_nom, destinataire_email, destinataire_nom,
             type_message, contenu, date_envoi)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (expediteur_email, expediteur_nom, destinataire_email, destinataire_nom,
          type_message, contenu, date_envoi))
    connection.commit()
    connection.close()


def lister_conversations(email):
    """
    Construit la liste des conversations de l'utilisateur : une ligne par
    "autre personne" avec qui il a échangé au moins un message, avec un
    aperçu du dernier message.
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT * FROM messages
        WHERE expediteur_email = ? OR destinataire_email = ?
        ORDER BY id DESC
    """, (email, email))
    tous_les_messages = cursor.fetchall()
    connection.close()

    # On garde uniquement le message le PLUS RÉCENT pour chaque contact.
    conversations = {}
    for message in tous_les_messages:
        if message["expediteur_email"] == email:
            autre_email = message["destinataire_email"]
            autre_nom = message["destinataire_nom"]
        else:
            autre_email = message["expediteur_email"]
            autre_nom = message["expediteur_nom"]

        # Comme les messages sont triés du plus récent au plus ancien, la
        # première fois qu'on rencontre ce contact, c'est son dernier message.
        if autre_email not in conversations:
            apercu = "🎤 Message vocal" if message["type_message"] == "vocal" else message["contenu"]
            conversations[autre_email] = {
                "email": autre_email,
                "nom": autre_nom,
                "dernier_message": apercu,
                "date": message["date_envoi"],
            }

    return list(conversations.values())


def lister_messages(email_a, email_b):
    """Renvoie tous les messages échangés entre deux utilisateurs, du plus ancien au plus récent."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT * FROM messages
        WHERE (expediteur_email = ? AND destinataire_email = ?)
           OR (expediteur_email = ? AND destinataire_email = ?)
        ORDER BY id ASC
    """, (email_a, email_b, email_b, email_a))
    messages = cursor.fetchall()
    connection.close()
    return messages


def lister_contacts_possibles(email_courant, type_courant):
    """
    Renvoie les comptes avec qui l'utilisateur courant peut DÉMARRER une
    nouvelle conversation, selon le cahier des charges :
    - un Club peut contacter tout le monde
    - un Particulier ne peut démarrer une conversation qu'avec un Club
      (il ne peut pas "visiter"/contacter directement un autre particulier)
    """
    connection = get_connection()
    cursor = connection.cursor()

    contacts = []

    cursor.execute("SELECT nom_club AS nom, email FROM clubs WHERE email != ?", (email_courant,))
    for club in cursor.fetchall():
        contacts.append({"email": club["email"], "nom": club["nom"], "type": "club"})

    if type_courant == "club":
        cursor.execute(
            "SELECT nom, prenoms, email FROM particuliers WHERE email != ?", (email_courant,)
        )
        for particulier in cursor.fetchall():
            nom_complet = f"{particulier['prenoms']} {particulier['nom']}"
            contacts.append({"email": particulier["email"], "nom": nom_complet, "type": "particulier"})

    connection.close()
    return contacts


# ---------------------------------------------------------------------------
# NOTIFICATIONS
# ---------------------------------------------------------------------------
def creer_notification(destinataire_email, type_notification, texte, lien):
    """Ajoute une notification pour un utilisateur (like ou message reçu)."""
    from datetime import datetime
    connection = get_connection()
    cursor = connection.cursor()
    date_notification = datetime.now().strftime("%d/%m/%Y %H:%M")
    cursor.execute("""
        INSERT INTO notifications (destinataire_email, type_notification, texte, lien, date_notification)
        VALUES (?, ?, ?, ?, ?)
    """, (destinataire_email, type_notification, texte, lien, date_notification))
    connection.commit()
    connection.close()


def lister_notifications(email):
    """Renvoie toutes les notifications d'un utilisateur, la plus récente en premier."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM notifications WHERE destinataire_email = ? ORDER BY id DESC", (email,)
    )
    notifications = cursor.fetchall()
    connection.close()
    return notifications


def compter_notifications_non_lues(email):
    """Compte les notifications pas encore lues (pour la petite pastille rouge)."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM notifications WHERE destinataire_email = ? AND lue = 0", (email,)
    )
    nombre = cursor.fetchone()[0]
    connection.close()
    return nombre


def marquer_notifications_lues(email):
    """Marque toutes les notifications d'un utilisateur comme lues."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE notifications SET lue = 1 WHERE destinataire_email = ?", (email,)
    )
    connection.commit()
    connection.close()


# ---------------------------------------------------------------------------
# PROFIL
# ---------------------------------------------------------------------------
def lister_posts_de(email):
    """Renvoie TOUS les posts (publics + privés) d'un utilisateur précis,
    pour les afficher sur sa propre page Profil."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM posts WHERE auteur_email = ? ORDER BY id DESC", (email,)
    )
    posts = cursor.fetchall()
    connection.close()
    return posts


def changer_visibilite_post(post_id, auteur_email):
    """
    Bascule un post entre "public" et "privé". Le `auteur_email` est vérifié
    pour être sûr qu'on ne modifie QUE ses propres posts.
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT visibilite FROM posts WHERE id = ? AND auteur_email = ?",
        (post_id, auteur_email)
    )
    post = cursor.fetchone()
    if post is not None:
        nouvelle_visibilite = "prive" if post["visibilite"] == "public" else "public"
        cursor.execute(
            "UPDATE posts SET visibilite = ? WHERE id = ?", (nouvelle_visibilite, post_id)
        )
        connection.commit()
    connection.close()


def modifier_club(email, nom_club, logo_url, pays, ligue):
    """Met à jour les informations modifiables d'un compte Club."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE clubs SET nom_club = ?, logo_url = ?, pays = ?, ligue = ?
        WHERE email = ?
    """, (nom_club, logo_url, pays, ligue, email))
    connection.commit()
    connection.close()


def modifier_particulier(email, nom, prenoms, nationalite, poste):
    """Met à jour les informations modifiables d'un compte Particulier."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE particuliers SET nom = ?, prenoms = ?, nationalite = ?, poste = ?
        WHERE email = ?
    """, (nom, prenoms, nationalite, poste, email))
    connection.commit()
    connection.close()


def changer_langue(type_compte, email, langue):
    """Enregistre la langue choisie par l'utilisateur dans son compte."""
    table = "clubs" if type_compte == "club" else "particuliers"
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"UPDATE {table} SET langue = ? WHERE email = ?", (langue, email))
    connection.commit()
    connection.close()


# ---------------------------------------------------------------------------
# ABONNEMENT OBLIGATOIRE (l'application est payante)
# - un "Compte Club" paie 1700Fr / mois
# - un "Compte particulier" paie 750Fr / mois
# - moyens de paiement acceptés : Wave, Moov Money, MTN Money
# ---------------------------------------------------------------------------
MOYENS_DE_PAIEMENT = ["Wave", "Moov Money", "MTN Money"]


def prix_abonnement(type_compte):
    """Renvoie le prix mensuel (en Fr) selon le type de compte."""
    return 1700 if type_compte == "club" else 750


def abonnement_est_actif(type_compte, email):
    """Renvoie True si le compte est à jour de son abonnement mensuel."""
    table = "clubs" if type_compte == "club" else "particuliers"
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"SELECT abonnement_actif FROM {table} WHERE email = ?", (email,))
    ligne = cursor.fetchone()
    connection.close()
    return ligne is not None and bool(ligne["abonnement_actif"])


def activer_abonnement(type_compte, email, moyen_paiement):
    """
    Marque l'abonnement comme payé.
    ⚠️ Ici, aucun vrai paiement n'est effectué (pas de connexion internet
    dans cet environnement de test) : on SIMULE la confirmation d'un
    paiement Wave / Moov Money / MTN Money. Pour un vrai lancement, il
    faudra brancher l'API du fournisseur choisi (Wave, MTN MoMo...) à la
    place de cette fonction.
    """
    table = "clubs" if type_compte == "club" else "particuliers"
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        f"UPDATE {table} SET abonnement_actif = 1, moyen_paiement = ? WHERE email = ?",
        (moyen_paiement, email)
    )
    connection.commit()
    connection.close()


def resilier_abonnement(type_compte, email):
    """Coupe l'accès à l'appli tant que l'abonnement n'est pas repayé."""
    table = "clubs" if type_compte == "club" else "particuliers"
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"UPDATE {table} SET abonnement_actif = 0 WHERE email = ?", (email,))
    connection.commit()
    connection.close()


# ---------------------------------------------------------------------------
# VISITE DE PROFIL
# - un Club peut visiter tout le monde (Clubs et Particuliers)
# - un Particulier ne peut visiter que les Clubs (pas un autre Particulier)
# ---------------------------------------------------------------------------
def peut_visiter(mon_type, type_du_compte_visite):
    if mon_type == "club":
        return True
    return type_du_compte_visite == "club"


def lister_posts_publics_de(email):
    """Comme lister_posts_de, mais uniquement les posts PUBLICS (pour
    affichage sur le profil de quelqu'un d'autre que soi-même)."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM posts WHERE auteur_email = ? AND visibilite = 'public' ORDER BY id DESC",
        (email,)
    )
    posts = cursor.fetchall()
    connection.close()
    return posts


# ---------------------------------------------------------------------------
# MARKET
# ---------------------------------------------------------------------------
def peut_publier_sur_market(type_compte, utilisateur):
    """
    D'après le cahier des charges :
    - un Club peut toujours publier (mettre un joueur en vente)
    - un Particulier ne peut publier que s'il est Agent ou Coach
      (un Joueur peut consulter le Market mais pas y publier)
    """
    if type_compte == "club":
        return True
    return utilisateur["profession"] in ("Agent", "Coach")


def creer_annonce_joueur(auteur_email, auteur_nom, logo_url, photo_joueur,
                          nom_joueur, poste, age, prix):
    """Un Club met un joueur sur le marché (façon mercato)."""
    from datetime import datetime
    connection = get_connection()
    cursor = connection.cursor()
    date_publication = datetime.now().strftime("%d/%m/%Y %H:%M")
    description = f"{poste} • {age} ans"
    cursor.execute("""
        INSERT INTO market_items
            (auteur_email, auteur_nom, logo_url, categorie, photo, nom_affiche, description, prix, date_publication)
        VALUES (?, ?, ?, 'joueur', ?, ?, ?, ?, ?)
    """, (auteur_email, auteur_nom, logo_url, photo_joueur, nom_joueur, description, prix, date_publication))
    connection.commit()
    connection.close()


def creer_annonce_recherche(auteur_email, auteur_nom, photo, texte_recherche):
    """Un Agent ou un Coach publie sa photo et ce qu'il recherche."""
    from datetime import datetime
    connection = get_connection()
    cursor = connection.cursor()
    date_publication = datetime.now().strftime("%d/%m/%Y %H:%M")
    cursor.execute("""
        INSERT INTO market_items
            (auteur_email, auteur_nom, logo_url, categorie, photo, nom_affiche, description, prix, date_publication)
        VALUES (?, ?, ?, 'recherche', ?, ?, ?, NULL, ?)
    """, (auteur_email, auteur_nom, photo, photo, auteur_nom, texte_recherche, date_publication))
    connection.commit()
    connection.close()


def lister_annonces_market():
    """Renvoie toutes les annonces du Market, la plus récente en premier."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM market_items ORDER BY id DESC")
    annonces = cursor.fetchall()
    connection.close()
    return annonces
{% extends "base.html" %}
{% block contenu %}
    <h1>Abonnement</h1>

    <p>
      "L'application Meet Foot est payante :"
        <strong>{{ prix }}Fr / mois</strong> pour ton type de compte.
    </p>

    {% if actif %}
        <p style="color:#2e7d32; font-weight:bold;">
             Ton abonnement est actif (payé via {{ moyen_actuel }}).
        </p>
        <form method="POST">
            <input type="hidden" name="action" value="resilier">
            <button type="submit" style="background:#c62828;">Résilier mon abonnement</button>
        </form>

    {% else %}
        <p style="color:#c62828; font-weight:bold;">
            Ton abonnement n'est pas à jour. Choisis un moyen de paiement
            pour continuer à utiliser l'application.
        </p>

        <form method="POST">
            <label>Moyen de paiement</label>
            <select name="moyen_paiement" required>
                {% for moyen in moyens %}
                    <option value="{{ moyen }}">{{ moyen }}</option>
                {% endfor %}
            </select>

            <button type="submit">Payer {{ prix }}Fr et activer mon compte</button>
        </form>

        <p style="color:#888; font-size:12px; margin-top:14px;">
            <em>Ceci est une version de démonstration : le paiement est
            simulé (pas de connexion internet dans cet environnement de
            test). Pour un vrai lancement, il faudra brancher l'API du
            fournisseur choisi (Wave, MTN MoMo, Moov Money...) à la place
            de cette simulation.</em>
        </p>

        <p><a href="{{ url_for('logout') }}">Se déconnecter</a></p>
    {% endif %}

    {% if actif %}
        <p><a href="{{ url_for('parametres') }}">← Retour aux paramètres</a></p>
    {% endif %}
{% endblock %}
{% extends "base.html" %}
{% block contenu %}
    {% if type_compte == "club" %}
        <div style="text-align:center; margin-bottom:14px;">
            {% if compte.logo_url %}
                <img src="{{ compte.logo_url }}" style="width:80px; height:80px; border-radius:50%; object-fit:cover;">
            {% endif %}
            <h1 style="margin:8px 0 0 0;">{{ compte.nom_club }}</h1>
            <p style="color:#666; margin:4px 0;">
                {{ compte.discipline }} · {{ compte.pays }}{% if compte.ligue %} · {{ compte.ligue }}{% endif %}
            </p>
        </div>
    {% else %}
        <div style="text-align:center; margin-bottom:14px;">
            <h1 style="margin:0;">{{ compte.prenoms }} {{ compte.nom }}</h1>
            <p style="color:#666; margin:4px 0;">
                {{ compte.profession }} · {{ compte.sport }}
                {% if compte.poste %} · {{ compte.poste }}{% endif %}
            </p>
            <p style="color:#888; font-size:13px;">{{ compte.nationalite }}</p>
        </div>
    {% endif %}

    <p style="text-align:center;">
        <a class="bouton" href="{{ url_for('conversation', autre_email=email_visite) }}">💬 Envoyer un message</a>
    </p>

    <h2>Publications</h2>

    {% if posts|length == 0 %}
        <p><em>Aucune publication publique pour le moment.</em></p>
    {% endif %}

    {% for post in posts %}
        <div style="background:white; padding:14px; border-radius:8px; margin-bottom:14px;">
            <span style="font-size:11px; color:#888;">{{ post.date_publication }}</span>

            {% if post.contenu_texte %}
                <p>{{ post.contenu_texte }}</p>
            {% endif %}

            {% if post.fichier_media %}
                {% if post.type_media == "video" %}
                    <video controls style="max-width:100%; border-radius:6px;">
                        <source src="{{ url_for('static', filename='uploads/' + post.fichier_media) }}">
                    </video>
                {% else %}
                    <img src="{{ url_for('static', filename='uploads/' + post.fichier_media) }}" style="max-width:100%; border-radius:6px;">
                {% endif %}
            {% elif post.image_url %}
                <img src="{{ post.image_url }}" style="max-width:100%; border-radius:6px;">
            {% endif %}
        </div>
    {% endfor %}
{% endblock %}
{% extends "base.html" %}
{% block contenu %}
    <h1>Accès non autorisé</h1>
    <p>
        🔒 En tant que Compte particulier, tu ne peux pas visiter le profil
        d'un autre Compte particulier ({{ nom }}). Tu peux uniquement
        visiter les profils des Comptes Club.
    </p>
    <p><a href="{{ url_for('accueil') }}">← Retour à l'accueil</a></p>
{% endblock %}
{% extends "base.html" %}
{% block contenu %}
    {% if type_compte == "club" %}
        <div style="text-align:center; margin-bottom:14px;">
            {% if compte.logo_url %}
                <img src="{{ compte.logo_url }}" style="width:80px; height:80px; border-radius:50%; object-fit:cover;">
            {% endif %}
            <h1 style="margin:8px 0 0 0;">{{ compte.nom_club }}</h1>
            <p style="color:#666; margin:4px 0;">
                {{ compte.discipline }} · {{ compte.pays }}{% if compte.ligue %} · {{ compte.ligue }}{% endif %}
            </p>
        </div>
    {% else %}
        <div style="text-align:center; margin-bottom:14px;">
            <h1 style="margin:0;">{{ compte.prenoms }} {{ compte.nom }}</h1>
            <p style="color:#666; margin:4px 0;">
                {{ compte.profession }} · {{ compte.sport }}
                {% if compte.poste %} · {{ compte.poste }}{% endif %}
            </p>
            <p style="color:#888; font-size:13px;">{{ compte.nationalite }}</p>
        </div>
    {% endif %}

    {% if compte.abonnement_actif %}
        <p style="text-align:center; color:#2e7d32;">✅ Abonnement à jour</p>
    {% endif %}

    <p style="text-align:center;">
        <a class="bouton" href="{{ url_for('parametres') }}"> Paramètres</a>
    </p>

    <h2>Mes publications</h2>

    {% if mes_posts|length == 0 %}
        <p><em>Tu n'as encore rien publié. Direction l'onglet Créer !</em></p>
    {% endif %}

    {% for post in mes_posts %}
        <div style="background:white; padding:14px; border-radius:8px; margin-bottom:14px;">
            <span style="font-size:11px; color:#888;">
                {{ "Public" if post.visibilite == "public" else "Privé" }} · {{ post.date_publication }}
            </span>

            {% if post.contenu_texte %}
                <p>{{ post.contenu_texte }}</p>
            {% endif %}

            {% if post.fichier_media %}
                {% if post.type_media == "video" %}
                    <video controls style="max-width:100%; border-radius:6px;">
                        <source src="{{ url_for('static', filename='uploads/' + post.fichier_media) }}">
                    </video>
                {% else %}
                    <img src="{{ url_for('static', filename='uploads/' + post.fichier_media) }}" style="max-width:100%; border-radius:6px;">
                {% endif %}
            {% elif post.image_url %}
                <img src="{{ post.image_url }}" style="max-width:100%; border-radius:6px;">
            {% endif %}

            <form method="POST" action="{{ url_for('basculer_visibilite_post', post_id=post.id) }}" style="margin-top:8px;">
                <button type="submit" style="background:#555;">
                    {{ "Rendre privé" if post.visibilite == "public" else "Rendre public" }}
                </button>
            </form>
        </div>
    {% endfor %}
{% endblock %}
<!--
base.html
---------
C'est le "moule" commun à toutes les pages : la barre de navigation en bas
(comme sur une vraie appli mobile) et le style général.
Les autres pages viennent s'insérer dans le bloc "contenu" ci-dessous.
-->
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Meet Foot</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding-bottom: 70px; /* laisse de la place pour la barre du bas */
            background: #f2f2f2;
        }
        .contenu {
            max-width: 500px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 { color: #1a1a1a; }
        input, select {
            width: 100%;
            padding: 10px;
            margin: 6px 0 14px 0;
            box-sizing: border-box;
            border: 1px solid #ccc;
            border-radius: 6px;
        }
        label { font-weight: bold; }
        button, .bouton {
            background: #2e7d32;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 15px;
            text-decoration: none;
            display: inline-block;
        }
        .erreur { color: #c62828; font-weight: bold; }

        /* Barre de navigation fixée en bas, comme sur mobile */
        .nav-bas {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            display: flex;
            justify-content: space-around;
            border-top: 1px solid #ddd;
            padding: 10px 0;
        }
        .nav-bas a {
            text-decoration: none;
            color: #333;
            font-size: 13px;
            text-align: center;
            position: relative;
        }
        .pastille {
            background: #c62828;
            color: white;
            border-radius: 50%;
            font-size: 10px;
            padding: 1px 5px;
            position: absolute;
            top: -6px;
            right: -10px;
        }
    </style>
</head>
<body>

    <div class="contenu">
        {% block contenu %}{% endblock %}
    </div>

    {% if session.get("email") and abonnement_ok %}
    <div class="nav-bas">
        <a href="{{ url_for('accueil') }}"><br>Accueil</a>
        <a href="{{ url_for('notifications') }}">
            {% if nb_notifs_non_lues > 0 %}<span class="pastille">{{ nb_notifs_non_lues }}</span>{% endif %}
            <br>Notif
        </a>
        <a href="{{ url_for('creer') }}"><br>Créer</a>
        <a href="{{ url_for('messagerie') }}"><br>Messages</a>
        <a href="{{ url_for('market') }}"><br>Market</a>
        <a href="{{ url_for('profil') }}"><br>Profil</a>
    </div>
    {% endif %}

</body>
</html>
# Meet Foot

## Ce que contient ce projet
- `app.py` : le serveur (toutes les routes / pages du site)
- `models.py` : toute la base de données (comptes, posts, likes, messages,
  notifications, annonces du Market)
- `templates/` : les pages HTML affichées
- `static/uploads/` : photos et vidéos publiées
- `static/audio/` : messages vocaux enregistrés
- `requirements.txt` : la bibliothèque Python nécessaire (Flask)

## Fonctionnalités déjà codées
- Page d'accueil avant connexion, choix "Compte Club" / "Compte particulier"
- Inscription Club (logo, nom, discipline, pays, ligue, email, mot de passe)
- Inscription Particulier (nom, prénoms, date de naissance, nationalité,
  profession, sport, poste si joueur, email, mot de passe)
- Connexion / déconnexion

Les **6 onglets** sont maintenant tous fonctionnels :
1. **Accueil** : fil d'actualité (texte, photo, vidéo), likes
2. **Notifications** : générées automatiquement lors d'un like ou d'un
   message reçu, avec pastille rouge sur l'icône 🔔 tant qu'elles ne sont
   pas lues
3. **Créer** : publication d'une photo, d'une vidéo ou d'un texte, avec
   choix de visibilité (public / privé)
4. **Messagerie** : liste des conversations, démarrage d'une nouvelle
   conversation (un Club peut contacter tout le monde, un Particulier
   uniquement les Clubs), messages texte **et vocaux** (micro du navigateur)
5. **Le Market** : les Clubs mettent des joueurs en vente (photo, nom,
   poste, âge, prix), les Agents/Coachs publient leur photo et ce qu'ils
   recherchent ; les Joueurs peuvent consulter mais pas publier ; boutons
   Acheter/Négocier qui ouvrent une conversation avec l'auteur de l'annonce
6. **Profil** : infos du compte, mes publications (avec bouton pour
   basculer public/privé), et Paramètres (changer mes infos, changer la
   langue, gérer l'abonnement Premium, se déconnecter)

## Comment le lancer
```bash
# 1. Se placer dans le dossier du projet
cd meet_foot

# 2. Installer Flask (une seule fois)
pip install -r requirements.txt

# 3. Lancer le serveur
python app.py

# 4. Ouvrir dans le navigateur
http://127.0.0.1:5000
```
Un fichier `meet_foot.db` sera créé automatiquement au premier lancement :
c'est ta base de données (tous les comptes et contenus y sont stockés).

## Nouveautés : abonnement obligatoire + visite de profil
- **L'application est payante** : après son inscription, chaque compte est
  redirigé vers une page de paiement obligatoire tant qu'il n'a pas réglé
  son abonnement mensuel (1700Fr pour un Club, 750Fr pour un Particulier),
  via Wave, Moov Money ou MTN Money. Sans abonnement actif, impossible
  d'accéder à un onglet de l'appli.
  Le paiement est **simulé** (pas de connexion internet dans cet
  environnement de test) : pour un vrai lancement, il faudra brancher
  l'API du fournisseur choisi à la place de la fonction
  `activer_abonnement()` dans `models.py`.
- **Visite de profil restreinte** : en cliquant sur le nom de quelqu'un
  (Accueil, Market, Messagerie), on arrive sur son profil public. Un Club
  peut visiter tout le monde ; un Particulier ne peut visiter que les
  Comptes Club (pas un autre Particulier).

## Idées pour aller plus loin
- un vrai panier d'achat sur le Market (au lieu d'ouvrir directement la
  messagerie)
- une vraie traduction de l'interface selon la langue choisie
- brancher un vrai fournisseur de paiement mobile money
- déployer l'appli en ligne pour que d'autres puissent la tester
