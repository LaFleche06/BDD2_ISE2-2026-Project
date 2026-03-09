# Projet EDE - Gestion des Notes et des Étudiants

Bienvenue dans le dépôt du projet EDE, une application complète (Frontend Web Flask + Backend API REST FastAPI) permettant la gestion scolaire (étudiants, professeurs, notes, matières, et classements).

Ce projet comporte deux composants principaux :
1. **L'API Backend (`/API`)** : Développée avec **FastAPI** et **SQLAlchemy**. Elle gère toute la logique métier, la base de données SQL Server et l'authentification (basée sur JWT).
2. **Le Client Web (`/Projet_BDD2`)** : Développé avec **Flask**. C'est le portail utilisateur (Front-end) qui consomme l'API pour afficher les tableaux de bord et les vues dédiées aux Administrateurs, Professeurs et Étudiants.

---

## 🏗️ Architecture et Déploiement

Le projet est conçu pour fonctionner en environnement **Local** (développement) ainsi qu'en environnement de **Production** découpé sur le cloud AWS.

### En Environnement de Production (AWS)
- **Base de données principale** : Hébergée sur **Amazon RDS** (SQL Server). Oubliez la gestion de l'infrastructure de la base de données, RDS s'occupe des sauvegardes, de la haute disponibilité et des correctifs.
- **Backend API (FastAPI)** : Déployé sur une instance **Amazon EC2**. Il se connecte de manière sécurisée à l'instance RDS. 

*(Le client web Flask peut être hébergé sur une autre instance EC2, sur Elastic Beanstalk, ou localement chez l'administrateur en pointant vers l'EC2 de l'API).*

---

## 🚀 1. Exécution en Local (Développement)

Pour faire tourner le projet sur votre propre machine (ex: Windows) :

### Pré-requis
- Python 3.10+
- Pilote ODBC 17 pour SQL Server installé sur votre machine.
- Une instance locale SQL Server (ou un accès à votre RDS de dev).

### Étape 1 : Configurer et Lancer l'API (FastAPI)
1. Ouvrez un terminal et placez-vous dans le dossier `/API`.
2. Créez et activez un environnement virtuel :
   ```bash
   python -m venv env
   # Sous Windows :
   env\Scripts\activate
   ```
3. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
4. Configuration de la base de données :
   - Assurez-vous que la chaîne de connexion (dsn) pointe vers votre base de données locale dans le fichier de config ou `.env`.
   - Lancez les migrations/scripts de création si la base est vide.
5. Démarrez le serveur uvicorn :
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   *L'API sera disponible sur `http://localhost:8000` et la doc Swagger sur `http://localhost:8000/docs`.*

### Étape 2 : Configurer et Lancer le Client Web (Flask)
1. Ouvrez un autre terminal et placez-vous dans le dossier `/Projet_BDD2`.
2. Activez le **même environnement virtuel** ou créez-en un nouveau et installez les dépendances :
   ```bash
   pip install flask requests
   ```
3. Configuration de l'accès à l'API :
   - Ouvrez le fichier `config.py` (ou équivalent) présent dans `Projet_BDD2/`.
   - Assurez-vous que la variable `API_BASE_URL` pointe bien sur `http://localhost:8000`.
4. Démarrez le serveur Flask :
   ```bash
   python app.py
   ```
   *Le portail Web sera accessible sur `http://localhost:5000`.*

---

## 🌍 2. Déploiement en Production (AWS EC2 + RDS)

### Étape 1 : Base de données (Amazon RDS)
1. Créez une instance Amazon RDS pour **Microsoft SQL Server**.
2. Récupérez le "Endpoint" (URL du cluster de la BD), le nom d'utilisateur et le mot de passe administrateur.
3. Configurez les **Security Groups** d'AWS pour que l'instance EC2 de votre API puisse communiquer sur le port 1433 de l'instance RDS.

### Étape 2 : L'API (Amazon EC2)
1. Lancez une instance Linux (Ubuntu par exemple) sur Amazon EC2.
2. Connectez-vous en SSH à l'instance EC2.
3. Installez Python, pip, ainsi que le **pilote ODBC 17 pour SQL Server** pour Linux.
   > *Sous Ubuntu, référez-vous [à la documentation Microsoft](https://learn.microsoft.com/fr-fr/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server) pour `msodbcsql17`.*
4. Clonez ce dépôt GitHub.
5. Allez dans le dossier `API/`, installez les packages (`pip install -r requirements.txt`).
6. Mettez à jour la chaîne de connexion SQLAlchemy avec les informations de votre RDS.
7. Lancez le serveur FastAPI en tâche de fond ou utilisant un gestionnaire comme **systemd** et **Gunicorn** (+ uvicorn workers) sur le port 80.

### Étape 3 : Le Client HTTP (Flask)
1. Déployez le client Flask (soit sur le même EC2, soit sur un autre).
2. Remplacez la valeur de `API_BASE_URL` dans le dossier `Projet_BDD2/` avec l'adresse IP publique ou le nom de domaine de l'instance EC2 hébergeant FastAPI (ex: `http://ec2-xx-xx-xx-xx.compute.amazonaws.com:8000`).

---

## 👷‍♂️ Fonctionnalités Principales

- **Administrateur** : Création et gestion des élèves, des profs, des classes et des matières. Affectations des professeurs aux matières. Visualisation des statistiques globales et import massif.
- **Professeur** : Tableau de bord de ses interventions. Saisie, modification et suppression des notes (une par une ou en traitement par lots) pour ses propres matières.
- **Étudiant** : Tableau de bord complet. Visualisation du rang, de sa moyenne pondérée (calculée en direct) et du statut d'admission.

## 🛠️ Stack Technique
- **Base de Données** : Microsoft SQL Server (Transact-SQL)
- **Backend API** : Python, FastAPI, SQLAlchemy, Pydantic, Uvicorn, PassLib, JWT
- **Frontend** : Python, Flask, Jinja2, HTML5/CSS3 natif
