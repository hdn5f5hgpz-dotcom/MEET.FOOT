# Meet Foot

## Ce que contient ce projet
- `app.py` : le serveur
- `models.py` : la base de donnees
- `templates/` : les pages HTML
- `static/uploads/` : photos et videos
- `static/audio/` : messages vocaux
- `requirements.txt` : Flask

## Fonctionnalites deja codees
- Page d'accueil avant connexion, choix Club / Particulier
- Inscription Club et Particulier
- Connexion / deconnexion
- Les 6 onglets :
1. Accueil : fil d'actualite, likes
2. Notifications : pastille rouge
3. Creer : photo, video, texte, public/prive
4. Messagerie : texte et vocaux
5. Le Market : Clubs vendent joueurs, Agents/Coachs cherchent
6. Profil : mes publications, parametres, abonnement

## Comment le lancer
pip install -r requirements.txt
python app.py
http://127.0.0.1:5000

## Abonnement
- Club : 1700Fr / mois
- Particulier : 750Fr / mois
- Wave / Moov Money / MTN Money (simule pour l'instant)
- Visite de profil : Club peut tout voir, Particulier seulement les Clubs