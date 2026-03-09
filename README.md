# Campus ENSAE EDE - Système de Gestion Scolaire

Bienvenue sur le dépôt du projet Campus ENSAE EDE.
Ce projet est une plateforme complète permettant la gestion de la scolarité : gestion des étudiants, professeurs, classes, matières, ainsi que la saisie et le calcul automatique des notes et des classements.

L'architecture est scindée en deux parties indépendantes communicant par requêtes HTTP :
1. **L'API Backend (`/API`)** : Un web service développé avec FastAPI et SQLAlchemy. Elle gère la logique métier, s'interface avec la base de données SQL Server, et gère l'authentification sécurisée via JWT.
2. **Le Portail Web Client (`/Projet_BDD2`)** : Une interface utilisateur Server-Side Rendered via Flask et Jinja2. C'est le portail où les différents acteurs (Administrateurs, Professeurs, Étudiants) se connectent pour consulter leurs tableaux de bord.

---

## Architecture et Déploiement en Production

L'infrastructure de production est distribuée et robuste :

- **Base de données (Amazon RDS)** :
  La base de données relationnelle (Microsoft SQL Server) est managée par AWS RDS, assurant la haute disponibilité.
- **Backend API FastAPI (Amazon EC2 + DuckDNS)** :
  Hébergée sur une instance Amazon EC2, l'API s'interface avec le RDS et est exposée via l'URL :
  [https://api-ensae-bdd2-ise2-2026.duckdns.org/docs](https://api-ensae-bdd2-ise2-2026.duckdns.org/docs)
- **Portail Web Flask (Render.com)** :
  L'application Flask est déployée sur Render. Elle consomme l'API déployée sur EC2. L'accès public se fait depuis :
  [https://campusensae.onrender.com/EDE/login](https://campusensae.onrender.com/EDE/login)

---

## Exécution en Local

### Pré-requis
- Python 3.10 ou supérieur.
- Un gestionnaire de base de données SQL Server local ou l'URL de l'instance RDS de test.
- Le Pilote ODBC 17 pour SQL Server installé sur la machine hôte.

### Lancer l'API FastAPI
1. Ouvrez un terminal et déplacez-vous dans le dossier de l'API :
   ```bash
   cd API
   ```
2. Créez et activez un environnement virtuel Python :
   ```bash
   python -m venv env
   env\Scripts\activate
   ```
3. Installez les paquets requis :
   ```bash
   pip install -r requirements.txt
   ```
4. Lancez le serveur de développement Uvicorn :
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   L'API écoute sur `http://localhost:8000` avec la documentation Swagger disponible sur `/docs`.

### Lancer le Client Web Flask
1. Ouvrez un second terminal, dans le dossier Web :
   ```bash
   cd Projet_BDD2
   ```
2. Activez l'environnement virtuel, puis installez les dépendances :
   ```bash
   pip install flask requests
   ```
3. Assurez-vous que l'application pointe sur l'API (p. ex. vérifier `config.py` ou `.env`).
4. Lancez le serveur Flask :
   ```bash
   python app.py
   ```
   Le portail est accessible sur `http://localhost:5000`.

---

## Fonctionnalités par Rôle

### 1. Administrateur
Responsable du système avec des droits étendus :
- Gestion des Utilisateurs : Création, suspension et réinitialisation des mots de passe.
- Gestion Pédagogique : Création des classes, des matières et affectations (Interventions).
- Statistiques et Tableaux de bord : Vision d'ensemble, taux de réussite, import en masse d'étudiants.

### 2. Professeur
Responsable pédagogique et de l'évaluation :
- Affectations : Visualisation des classes et matières assignées.
- Gestion des Notes : Saisie individuelle, saisie en masse, édition et suppression des évaluations.

### 3. Étudiant
Utilisateur de la plateforme pour le suivi scolaire :
- Tableau de Bord : Synthèse des informations académiques.
- Bulletin Détaillé : Rapport complet avec historique par matière.
- Rang Officiel : Position de l'étudiant dans le classement de sa classe.
