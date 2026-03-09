# 🎓 Campus ENSAE EDE - Système de Gestion Scolaire

Bienvenue sur le dépôt du projet **Campus ENSAE EDE** ! 🚀
Ce projet est une plateforme complète permettant la gestion de la scolarité : gestion des étudiants, professeurs, classes, matières, ainsi que la saisie et le calcul automatique des notes et classements.

L'architecture est moderne et scindée en deux parties indépendantes communicant par requêtes HTTP :
1. **L'API Backend (`/API`)** : Un web service ultra-rapide et robuste développé avec **FastAPI** et **SQLAlchemy**. Elle gère toute la logique métier, s'interface avec la base de données SQL Server, et gère l'authentification sécurisée (Jetons JWT).
2. **Le Portail Web Client (`/Projet_BDD2`)** : Une interface utilisateur claire, fluide et entièrement **Server-Side Rendered** via **Flask & Jinja2**. C'est le portail où les différents acteurs (Administrateurs, Professeurs, Étudiants) se connectent pour consulter leurs tableaux de bord.

---

## 🏗️ Architecture et Déploiement en Production

L'infrastructure de production a été pensée pour être distribuée, robuste et disponible publiquement via des URLs dédiées :

- **🗄️ Base de données (Amazon RDS)** :
  La base de données relationnelle (Microsoft SQL Server) est managée directement par AWS RDS. Nous nous affranchissons ainsi de la gestion des sauvegardes manuelles et des problématiques de haute disponibilité.
- **⚙️ Backend API FastAPI (Amazon EC2 + DuckDNS)** :
  Hébergée sur une instance **Amazon EC2**, l'API est le cœur logique. Elle s'interface directement et sécuritairement avec le RDS. Elle est exposée via le domaine personnalisé : 
  👉 **[https://api-ensae-bdd2-ise2-2026.duckdns.org/docs](https://api-ensae-bdd2-ise2-2026.duckdns.org/docs)**
- **🌐 Portail Web Flask (Render.com)** :
  L'application Flask (le Frontend) est déployée de manière Serverless/PaaS sur **Render**. Elle consomme simplement l'URL de l'API déployée sur EC2 pour afficher les données. L'accès public se fait depuis :
  👉 **[https://campusensae.onrender.com/EDE/login](https://campusensae.onrender.com/EDE/login)**

---

## 💻 Exécution en Local (Guide de Développement)

Si vous souhaitez contribuer ou faire tourner ce projet sur votre propre machine, suivez ces étapes. L'API et le portail fonctionneront indépendamment sur différents ports locaux.

### Pré-requis
- **Python 3.10+** d'installé.
- Un gestionnaire de base de données SQL Server local ou l'URL de votre instance RDS de test.
- Le **Pilote ODBC 17 pour SQL Server** installé sur votre machine (nécessaire pour SQLAlchemy/PyODBC).

### Étape 1 : Configurer et Lancer l'API FastAPI
1. Ouvrez un premier terminal et déplacez-vous dans le dossier de l'API :
   ```bash
   cd API
   ```
2. Créez un environnement virtuel Python et activez-le :
   ```bash
   python -m venv env
   # Sur Windows :
   env\Scripts\activate
   ```
3. Installez les paquets requis :
   ```bash
   pip install -r requirements.txt
   ```
4. Lancez le serveur de développement Uvicorn (avec redémarrage automatique) :
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   *✨ L'API écoute maintenant sur `http://localhost:8000` ! (Swagger disponible sur `/docs`)*

### Étape 2 : Configurer et Lancer le Client Web Flask
1. Ouvrez un second terminal, et allez dans le dossier Web :
   ```bash
   cd Projet_BDD2
   ```
2. Activez le même environnement virtuel que tout à l'heure, ou créez-en un nouveau, puis installez les requirements :
   ```bash
   pip install flask requests
   ```
3. *(Optionnel)* Modifiez le fichier de configuration (p. ex. `config.py`) pour vous assurer que l'application pointe bien sur l'API locale. La variable `API_BASE_URL` doit valoir `http://localhost:8000`.
4. Lancez le serveur Flask :
   ```bash
   python app.py
   ```
   *🎉 Le portail est accessible ! Ouvrez votre navigateur sur `http://localhost:5000` et connectez-vous.*

---

## 🌟 Fonctionnalités par Rôle

### 🛡️ 1. Administrateurs
Gardiens du système, ils possèdent les droits absolus de création et de gestion scolaire.
*   **Gestions des Utilisateurs** : Création, suspension et réinitialisation de mots de passe pour tous les professeurs et étudiants.
*   **Gestion Pédagogique** : Création des classes, des matières, et rattachement des Professeurs ↔ Matières ↔ Classes (`Interventions`).
*   **Statistiques et Tableaux de bord** : Vision d'ensemble macroscopique, taux de réussite, remplissage des notes, import d'étudiants par lots.

### 👨‍🏫 2. Professeurs
Acteurs clés de la pédagogie, responsables de l'évaluation des étudiants.
*   **Interventions** : Vue sur les classes et matières qui leur sont attribuées.
*   **Gestion des notes** :
    *   Saisie des notes individuelles.
    *   Mode de **saisie massive "batch"** (type tableur) pour une classe complète !
    *   Modification/Suppression des évaluations qu'ils ont effectuées.

### 🎓 3. Étudiants
Consommateurs de la plateforme, pour le suivi de leur scolarité.
*   **Tableau de bord personnel** : Synthèse de leurs informations (Moyenne générale pondérée, calculée dynamiquement).
*   **Bulletin détaillé** : Vue par matière avec les notes, classements partiels, et les coefficients.
*   **Rang Officiel** : Visualisation en temps réel de la position qu'ils occupent au sein de leur classe (Ex: 1er / 24).

---
*Ce projet (API FastAPI x Client Flask) a traversé divers défis d'architecture distribuée pour offrir une expérience fluide, rapide et moderne ! N'hésitez pas à parcourir le code et proposer des Pull Requests.* 🚀
