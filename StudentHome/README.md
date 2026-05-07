# StudentHome Marrakech

StudentHome Marrakech est une application web Flask simple pour gérer des logements étudiants destinés aux étudiants de l'UCA.

## Fonctionnalités

- Inscription et connexion avec rôles : étudiant, propriétaire, administrateur limité
- Connexion étudiant par code Massar
- Validation du code Massar et mot de passe renforcé à l'inscription
- Recherche de logements par faculté, quartier, prix et disponibilité
- Consultation libre de l'accueil, des annonces et des détails sans connexion
- Connexion ou inscription obligatoire seulement pour interagir : message, réservation, paiement, avis
- Demande de réservation et suivi des statuts
- Paiement sécurisé simulé par QR Code
- Avis après réservation confirmée ou terminée
- Ajout, modification et suppression d'annonces par le propriétaire
- Tableau admin réservé à `redakouchtam@icloud.com`

## Installation

Ouvrir un terminal dans le dossier `StudentHome`, puis lancer :

```bash
pip install -r requirements.txt
python app.py
```

Ensuite, ouvrir l'adresse affichée par Flask, généralement :

```text
http://127.0.0.1:5000
```

Lien direct nommé :

```text
http://127.0.0.1:5000/studenthome-marrakech
```

## Verification email et SMS

StudentHome ne montre jamais les codes de verification dans l'interface. Pour que les utilisateurs recoivent vraiment les codes par email, creez un fichier `.env` a la racine du projet avec les variables ci-dessous. Avec Gmail, il faut utiliser un mot de passe d'application, pas le mot de passe normal du compte.

Si SMTP n'est pas configure, aucun compte public n'est cree : l'utilisateur doit recevoir le code par email et le saisir avant que son compte soit enregistre comme verifie.

Variables email SMTP :

```text
STUDENTHOME_SMTP_HOST=smtp.gmail.com
STUDENTHOME_SMTP_PORT=587
STUDENTHOME_SMTP_USER=votre_email@gmail.com
STUDENTHOME_SMTP_PASSWORD=mot_de_passe_application
STUDENTHOME_SMTP_SENDER=votre_email@gmail.com
```

Apres configuration SMTP, chaque nouvel utilisateur inscrit recoit automatiquement un email avec le formulaire Google Forms StudentHome. L'administrateur peut aussi renvoyer ce formulaire a tous les utilisateurs depuis le dashboard admin.

Sur Render, ajoutez ces variables dans `Environment` du service web, puis redeployez. Sans ces variables, Gmail ne pourra pas envoyer les codes.

Variables SMS, selon le fournisseur choisi :

```text
STUDENTHOME_SMS_URL=https://api.votre-fournisseur-sms.com/send
STUDENTHOME_SMS_API_KEY=votre_cle_api
```

## AccÃ¨s depuis Internet

Pour ouvrir StudentHome depuis n'importe quel appareil, mÃªme hors du mÃªme Wi-Fi, l'application doit Ãªtre hÃ©bergÃ©e en ligne.

Option simple avec Render :

1. CrÃ©er un compte sur Render.
2. Envoyer le dossier `StudentHome` sur GitHub.
3. CrÃ©er un nouveau `Web Service` depuis le dÃ©pÃ´t GitHub.
4. Utiliser ces commandes :

```bash
pip install -r requirements.txt
waitress-serve --host=0.0.0.0 --port=$PORT app:app
```

Le fichier `render.yaml` est aussi prÃªt pour un dÃ©ploiement automatique avec le nom :

```text
studenthome-marrakech
```

L'adresse publique ressemblera Ã  :

```text
https://studenthome-marrakech.onrender.com
```

Pour taper exactement `studenthome-marrakech` sans extension, il faut configurer un DNS privÃ©, un routeur, ou le fichier `hosts` de chaque appareil. Sur Internet public, un vrai nom de domaine est nÃ©cessaire, par exemple :

```text
studenthome-marrakech.com
```

## Comptes de test

- Étudiant : `G123456789` / `Etudiant@123`
- Propriétaire : `youssef@mail.com` / `test123`
- Administrateur : `redakouchtam@icloud.com` / `Admin@12345`

## Ouvrir dans VS Code

1. Ouvrir VS Code.
2. Cliquer sur `File > Open Folder`.
3. Choisir le dossier `StudentHome`.
4. Ouvrir un terminal intégré avec `Terminal > New Terminal`.
5. Exécuter les commandes d'installation et de lancement.

## Structure

```text
StudentHome/
├── app.py
├── requirements.txt
├── database.db
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── images/
└── templates/
```

La base `database.db` est créée automatiquement au premier lancement avec des données d'exemple.
