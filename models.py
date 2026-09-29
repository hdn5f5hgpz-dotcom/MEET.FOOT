import sqlite3
DB_NAME = "meet_foot.db"

def get_connection():
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS clubs (id INTEGER PRIMARY KEY AUTOINCREMENT, nom_club TEXT NOT NULL, logo_url TEXT, discipline TEXT NOT NULL, pays TEXT NOT NULL, ligue TEXT, email TEXT UNIQUE NOT NULL, mot_de_passe TEXT NOT NULL)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS particuliers (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT NOT NULL, prenoms TEXT NOT NULL, date_naissance TEXT NOT NULL, nationalite TEXT NOT NULL, profession TEXT NOT NULL, sport TEXT NOT NULL, poste TEXT, email TEXT UNIQUE NOT NULL, mot_de_passe TEXT NOT NULL)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, auteur_type TEXT NOT NULL, auteur_email TEXT NOT NULL, auteur_nom TEXT NOT NULL, contenu_texte TEXT, image_url TEXT, date_publication TEXT NOT NULL)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS likes (id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER NOT NULL, email_utilisateur TEXT NOT NULL, UNIQUE(post_id, email_utilisateur))""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, expediteur_email TEXT NOT NULL, expediteur_nom TEXT NOT NULL, destinataire_email TEXT NOT NULL, destinataire_nom TEXT NOT NULL, type_message TEXT NOT NULL, contenu TEXT NOT NULL, date_envoi TEXT NOT NULL)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY AUTOINCREMENT, destinataire_email TEXT NOT NULL, type_notification TEXT NOT NULL, texte TEXT NOT NULL, lien TEXT NOT NULL, date_notification TEXT NOT NULL, lue INTEGER NOT NULL DEFAULT 0)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS market_items (id INTEGER PRIMARY KEY AUTOINCREMENT, auteur_email TEXT NOT NULL, auteur_nom TEXT NOT NULL, logo_url TEXT, categorie TEXT NOT NULL, photo TEXT, nom_affiche TEXT NOT NULL, description TEXT, prix TEXT, date_publication TEXT NOT NULL)""")
    connection.commit()
    connection.close()
    ajouter_colonne_si_absente("posts", "type_media", "TEXT")
    ajouter_colonne_si_absente("posts", "fichier_media", "TEXT")
    ajouter_colonne_si_absente("posts", "visibilite", "TEXT NOT NULL DEFAULT 'public'")
    ajouter_colonne_si_absente("clubs", "premium", "INTEGER NOT NULL DEFAULT 0")
    ajouter_colonne_si_absente("clubs", "langue", "TEXT NOT NULL DEFAULT 'Francais'")
    ajouter_colonne_si_absente("particuliers", "premium", "INTEGER NOT NULL DEFAULT 0")
    ajouter_colonne_si_absente("particuliers", "langue", "TEXT NOT NULL DEFAULT 'Francais'")
    ajouter_colonne_si_absente("clubs", "abonnement_actif", "INTEGER NOT NULL DEFAULT 0")
    ajouter_colonne_si_absente("clubs", "moyen_paiement", "TEXT")
    ajouter_colonne_si_absente("particuliers", "abonnement_actif", "INTEGER NOT NULL DEFAULT 0")
    ajouter_colonne_si_absente("particuliers", "moyen_paiement", "TEXT")

def ajouter_colonne_si_absente(table, colonne, type_sql):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {colonne} {type_sql}")
        connection.commit()
    except sqlite3.OperationalError:
        pass
    connection.close()

def creer_club(nom_club, logo_url, discipline, pays, ligue, email, mot_de_passe):
    c = get_connection(); c.execute("INSERT INTO clubs (nom_club, logo_url, discipline, pays, ligue, email, mot_de_passe) VALUES (?,?,?,?,?,?,?)", (nom_club, logo_url, discipline, pays, ligue, email, mot_de_passe)); c.commit(); c.close()

def creer_particulier(nom, prenoms, date_naissance, nationalite, profession, sport, poste, email, mot_de_passe):
    c = get_connection(); c.execute("INSERT INTO particuliers (nom, prenoms, date_naissance, nationalite, profession, sport, poste, email, mot_de_passe) VALUES (?,?,?,?,?,?,?,?,?)", (nom, prenoms, date_naissance, nationalite, profession, sport, poste, email, mot_de_passe)); c.commit(); c.close()

def trouver_utilisateur_par_email(email):
    c = get_connection(); cur = c.cursor(); cur.execute("SELECT * FROM clubs WHERE email =?", (email,)); club = cur.fetchone();
    if club is not None: c.close(); return "club", club
    cur.execute("SELECT * FROM particuliers WHERE email =?", (email,)); part = cur.fetchone(); c.close();
    if part is not None: return "particulier", part
    return None, None

def nom_affichage(type_compte, utilisateur):
    return utilisateur["nom_club"] if type_compte == "club" else f"{utilisateur['prenoms']} {utilisateur['nom']}"

def creer_post(auteur_type, auteur_email, auteur_nom, contenu_texte, image_url, type_media=None, fichier_media=None, visibilite="public"):
    from datetime import datetime; c = get_connection(); date_pub = datetime.now().strftime("%d/%m/%Y %H:%M"); c.execute("INSERT INTO posts (auteur_type, auteur_email, auteur_nom, contenu_texte, image_url, type_media, fichier_media, visibilite, date_publication) VALUES (?,?,?,?,?,?,?,?,?)", (auteur_type, auteur_email, auteur_nom, contenu_texte, image_url, type_media, fichier_media, visibilite, date_pub)); c.commit(); c.close()

def lister_posts(email_utilisateur_courant):
    c = get_connection(); cur = c.cursor(); cur.execute("SELECT * FROM posts WHERE visibilite = 'public' OR auteur_email =? ORDER BY id DESC", (email_utilisateur_courant,)); posts_bruts = cur.fetchall(); posts = []
    for post in posts_bruts:
        cur.execute("SELECT COUNT(*) FROM likes WHERE post_id =?", (post["id"],)); nb = cur.fetchone()[0]
        cur.execute("SELECT 1 FROM likes WHERE post_id =? AND email_utilisateur =?", (post["id"], email_utilisateur_courant)); deja = cur.fetchone() is not None
        d = dict(post); d["nombre_likes"] = nb; d["deja_like"] = deja; posts.append(d)
    c.close(); return posts

def recuperer_post(post_id):
    c = get_connection(); cur = c.cursor(); cur.execute("SELECT * FROM posts WHERE id =?", (post_id,)); p = cur.fetchone(); c.close(); return p

def toggle_like(post_id, email_utilisateur):
    c = get_connection(); cur = c.cursor(); cur.execute("SELECT id FROM likes WHERE post_id =? AND email_utilisateur =?", (post_id, email_utilisateur)); like_ex = cur.fetchone()
    if like_ex is not None: cur.execute("DELETE FROM likes WHERE id =?", (like_ex["id"],)); action = "suppression"
    else: cur.execute("INSERT INTO likes (post_id, email_utilisateur) VALUES (?,?)", (post_id, email_utilisateur)); action = "ajout"
    c.commit(); c.close(); return action

def envoyer_message(exp_email, exp_nom, dest_email, dest_nom, type_msg, contenu):
    from datetime import datetime; c = get_connection(); date_envoi = datetime.now().strftime("%d/%m/%Y %H:%M"); c.execute("INSERT INTO messages (expediteur_email, expediteur_nom, destinataire_email, destinataire_nom, type_message, contenu, date_envoi) VALUES (?,?,?,?,?,?,?)", (exp_email, exp_nom, dest_email, dest_nom, type_msg, contenu, date_envoi)); c.commit(); c.close()

def lister_conversations(email):
    c = get_connection(); cur = c.cursor(); cur.execute("SELECT * FROM messages WHERE expediteur_email =? OR destinataire_email =? ORDER BY id DESC", (email, email)); msgs = cur.fetchall(); c.close(); conv = {}
    for m in msgs:
        autre_email = m["destinataire_email"] if m["expediteur_email"] == email else m["expediteur_email"]
        autre_nom = m["destinataire_nom"] if m["expediteur_email"] == email else m["expediteur_nom"]
        if autre_email not in conv: apercu = "Message vocal" if m["type_message"] == "vocal" else m["contenu"]; conv[autre_email] = {"email": autre_email, "nom": autre_nom, "dernier_message": apercu, "date": m["date_envoi"]}
    return list(conv.values())

def lister_messages(email_a, email_b):
    c = get_connection(); cur = c.cursor(); cur.execute("SELECT * FROM messages WHERE (expediteur_email =? AND destinataire_email =?) OR (expediteur_email =? AND destinataire_email =?) ORDER BY id ASC", (email_a, email_b, email_b, email_a)); msgs = cur.fetchall(); c.close(); return msgs

def lister_contacts_possibles(email_courant, type_courant):
    c = get_connection(); cur = c.cursor(); contacts = []; cur.execute("SELECT nom_club AS nom, email FROM clubs WHERE email!=?", (email_courant,));
    for club in cur.fetchall(): contacts.append({"email": club["email"], "nom": club["nom"], "type": "club"})
    if type_courant == "club":
        cur.execute("SELECT nom, prenoms, email FROM particuliers WHERE email!=?", (email_courant,));
        for p in cur.fetchall(): contacts.append({"email": p["email"], "nom": f"{p['prenoms']} {p['nom']}", "type": "particulier"})
    c.close(); return contacts

def creer_notification(dest_email, type_notif, texte, lien):
    from datetime import datetime; c = get_connection(); date_notif = datetime.now().strftime("%d/%m/%Y %H:%M"); c.execute("INSERT INTO notifications (destinataire_email, type_notification, texte, lien, date_notification) VALUES (?,?,?,?,?)", (dest_email, type_notif, texte, lien, date_notif)); c.commit(); c.close()

def lister_notifications(email):
    c = get_connection(); cur = c.cursor(); cur.execute("SELECT * FROM notifications WHERE destinataire_email =? ORDER BY id DESC", (email,)); n = cur.fetchall(); c.close(); return n

def compter_notifications_non_lues(email):
    c = get_connection(); cur = c.cursor(); cur.execute("SELECT COUNT(*) FROM notifications WHERE destinataire_email =? AND lue = 0", (email,)); nb = cur.fetchone()[0]; c.close(); return nb

def marquer_notifications_lues(email):
    c = get_connection(); c.execute("UPDATE notifications SET lue = 1 WHERE destinataire_email =?", (email,)); c.commit(); c.close()

def lister_posts_de(email):
    c = get_connection(); cur = c.cursor(); cur.execute("SELECT * FROM posts WHERE auteur_email =? ORDER BY id DESC", (email,)); p = cur.fetchall(); c.close(); return p

def changer_visibilite_post(post_id, auteur_email):
    c = get_connection(); cur = c.cursor(); cur.execute("SELECT visibilite FROM posts WHERE id =? AND auteur_email =?", (post_id, auteur_email)); post = cur.fetchone()
    if post is not None: nouv = "prive" if post["visibilite"] == "public" else "public"; cur.execute("UPDATE posts SET visibilite =? WHERE id =?", (nouv, post_id)); c.commit()
    c.close()

def modifier_club(email, nom_club, logo_url, pays, ligue):
    c = get_connection(); c.execute("UPDATE clubs SET nom_club =?, logo_url =?, pays =?, ligue =? WHERE email =?", (nom_club, logo_url, pays, ligue, email)); c.commit(); c.close()

def modifier_particulier(email, nom, prenoms, nationalite, poste):
    c = get_connection(); c.execute("UPDATE particuliers SET nom =?, prenoms =?, nationalite =?, poste =? WHERE email =?", (nom, prenoms, nationalite, poste, email)); c.commit(); c.close()

def changer_langue(type_compte, email, langue):
    table = "clubs" if type_compte == "club" else "particuliers"; c = get_connection(); c.execute(f"UPDATE {table} SET langue =? WHERE email =?", (langue, email)); c.commit(); c.close()

MOYENS_DE_PAIEMENT = ["Wave", "Moov Money", "MTN Money"]
def prix_abonnement(type_compte): return 1700 if type_compte == "club" else 750
def abonnement_est_actif(type_compte, email):
    table = "clubs" if type_compte == "club" else "particuliers"; c = get_connection(); cur = c.cursor(); cur.execute(f"SELECT abonnement_actif FROM {table} WHERE email =?", (email,)); ligne = cur.fetchone(); c.close(); return ligne is not None and bool(ligne["abonnement_actif"])
def activer_abonnement(type_compte, email, moyen_paiement):
    table = "clubs" if type_compte == "club" else "particuliers"; c = get_connection(); c.execute(f"UPDATE {table} SET abonnement_actif = 1, moyen_paiement =? WHERE email =?", (moyen_paiement, email)); c.commit(); c.close()
def resilier_abonnement(type_compte, email):
    table = "clubs" if type_compte == "club" else "particuliers"; c = get_connection(); c.execute(f"UPDATE {table} SET abonnement_actif = 0 WHERE email =?", (email,)); c.commit(); c.close()
def peut_visiter(mon_type, type_visite): return True if mon_type == "club" else type_visite == "club"
def lister_posts_publics_de(email):
    c = get_connection(); cur = c.cursor(); cur.execute("SELECT * FROM posts WHERE auteur_email =? AND visibilite = 'public' ORDER BY id DESC", (email,)); p = cur.fetchall(); c.close(); return p
def peut_publier_sur_market(type_compte, utilisateur): return True if type_compte == "club" else utilisateur["profession"] in ("Agent", "Coach")
def creer_annonce_joueur(auteur_email, auteur_nom, logo_url, photo_joueur, nom_joueur, poste, age, prix):
    from datetime import datetime; c = get_connection(); date_pub = datetime.now().strftime("%d/%m/%Y %H:%M"); desc = f"{poste} - {age} ans"; c.execute("INSERT INTO market_items (auteur_email, auteur_nom, logo_url, categorie, photo, nom_affiche, description, prix, date_publication) VALUES (?,?,?, 'joueur',?,?,?,?,?)", (auteur_email, auteur_nom, logo_url, photo_joueur, nom_joueur, desc, prix, date_pub)); c.commit(); c.close()
def creer_annonce_recherche(auteur_email, auteur_nom, photo, texte_recherche):
    from datetime import datetime; c = get_connection(); date_pub = datetime.now().strftime("%d/%m/%Y %H:%M"); c.execute("INSERT INTO market_items (auteur_email, auteur_nom, logo_url, categorie, photo, nom_affiche, description, prix, date_publication) VALUES (?,?,?, 'recherche',?,?,?, NULL,?)", (auteur_email, auteur_nom, photo, photo, auteur_nom, texte_recherche, date_pub)); c.commit(); c.close()
def lister_annonces_market():
    c = get_connection(); cur = c.cursor(); cur.execute("SELECT * FROM market_items ORDER BY id DESC"); annonces = cur.fetchall(); c.close(); return annonces