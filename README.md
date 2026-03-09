# Campus ENSAE EDE - Système de Gestion Scolaire

Bienvenue sur le dépôt du projet Campus ENSAE EDE.
Ce projet est une plateforme complète permettant la gestion de la scolarité : gestion des étudiants, professeurs, classes, matières, ainsi que la saisie et le calcul automatique des notes et des classements.

L'architecture est scindée en deux parties indépendantes communicant par requêtes HTTP :
1. **L'API Backend (`/API`)** : Un web service développé avec FastAPI et SQLAlchemy. Elle gère la logique métier, s'interface avec la base de données SQL Server (AWS RDS), et gère l'authentification sécurisée via JWT.
2. **Le Portail Web Client (`/Projet_BDD2`)** : Une interface utilisateur Server-Side Rendered via Flask et Jinja2. C'est le portail où les différents acteurs (Administrateurs, Professeurs, Étudiants) se connectent pour consulter leurs tableaux de bord.

---

## Aperçu de l'application

| Portail Web (Flask) | API REST (FastAPI / Swagger) |
|---|---|
| ![Page de connexion](https://raw.githubusercontent.com/LaFleche06/BDD2_ISE2-2026-Project/main/docs/screenshot_login.png) | ![Swagger UI](https://raw.githubusercontent.com/LaFleche06/BDD2_ISE2-2026-Project/main/docs/screenshot_api.png) |

![Tableau de bord Admin](https://raw.githubusercontent.com/LaFleche06/BDD2_ISE2-2026-Project/main/docs/screenshot_dashboard.png)

---

## Comptes de démonstration

| Rôle | Email | Mot de passe |
|---|---|---|
| Administrateur | `admin@ensae.sn` | `admin123` |
| Enseignant | `prof@ensae.sn` | `prof123` |
| Étudiant | `etudiant@ensae.sn` | `etu123` |

---

## Architecture et Déploiement en Production

L'infrastructure de production est distribuée et robuste, reposant sur AWS et des services cloud modernes.

### 1. Base de données : Amazon RDS for SQL Server
Le choix s'est porté sur **Amazon RDS (Relational Database Service)** for SQL Server (édition Express, Free Tier) au lieu d'une instance EC2 classique (IaaS). 
RDS étant un service PaaS, AWS prend en charge l'installation du moteur, les sauvegardes automatisées, les mises à jour et la surveillance. Cette solution supprime la charge d'administration système.

**Configuration de l'instance RDS :**
- Moteur : Microsoft SQL Server Express Edition.
- Instance : .
- Stockage : 20 Gio SSD, mise à l'échelle automatique désactivée pour maîtriser les coûts.
- Accès public activé pour permettre les connexions depuis l'API.
- Sécurité : Le port  (SQL Server) est ouvert au niveau du groupe de sécurité. La sécurité repose sur l'authentification forte interne au moteur SQL Server.

**Migration des données depuis l'environnement local vers RDS :**
La base a été migrée via un **Script SQL complet (Schema and data)** généré par *SQL Server Management Studio (SSMS)*. Cette méthode a été privilégiée pour sa simplicité par rapport à AWS DMS.
Le script  contenant la définition complète (tables, vues , procédures stockées, données) a été exécuté directement sur la connexion RDS depuis SSMS, reconstituant ainsi la base de données à l'identique sur le cloud AWS.

### 2. Backend API : FastAPI sur Amazon EC2
L'application web ne se connecte pas directement à la base de données. Une couche **API REST** intermédiaire développée avec **FastAPI** a été introduite.
L'API sert de point d'entrée unique, s'assure des calculs complexes et met en place des mesures de sécurité comme l'authentification JWT (JSON Web Token). FastAPI génère également une documentation interactive (Swagger) automatiquement via OpenAPI sur la route .

**Hébergement et Déploiement sur AWS EC2 avec Nginx et Systemd :**
L'API HTTP est hébergée sur une instance **Amazon EC2** avec la configuration de production suivante :
- **Serveur d'application :**  exécuté depuis un environnement virtuel Python ().
- **Supervision (Systemd) :** L'API tourne en tant que service d'arrière-plan  (). Cette supervision assure que le serveur FastAPI démarre automatiquement avec la machine et est relancé en cas de défaillance imprévue.
- **Reverse Proxy (Nginx) :** Nginx réceptionne les requêtes externes sur les ports 80 (HTTP) et 443 (HTTPS) pour les rediriger vers le processus local  fonctionnant sur le port 8000 ().
- **Sécurité SSL/TLS (Let's Encrypt) :** La communication est sécurisée de bout en bout en HTTPS. Le certificat SSL a été généré via **Certbot** pour le nom de domaine dynamique .

Cette infrastructure garantit un déploiement \”production-ready\”. La publication d'une mise à jour de l'API se résume à une commande Already up to date. suivie de .

### 3. Portail Web Client : Flask sur Render.com
Le front-end, développé en **Flask**, tourne de manière server-side-rendered. Il est déployé sur **Render.com**, une plateforme SaaS reconnue.
- **Intégration continue :** Le déploiement s'y effectue par connexion native au dépôt GitHub (webhook sur la branche ).
- **Sécurité :** Les identifiants, JWT Secret et les URL (endpoints) de l'API EC2 sont uniquement renseignés dans le gestionnaire de variables d'environnement de Render.com. Ils ne sont jamais poussés sur Git.
- L'URL publique de l'application est : [https://campusensae.onrender.com/EDE/login](https://campusensae.onrender.com/EDE/login)

### 4. Organisation du travail (Git et GitHub)
Le projet applique des bonnes pratiques de versions avec Git pour un travail d'équipe fluide :
- **Branches de développement :** La branche  centralise le code prêt pour la production. Chaque nouvelle implémentation est élaborée dans une branche de type  puis mergée.
- **Masquage des secrets :** Les données sensibles sont confinées dans le fichier  sur chaque poste (renseigné dans le ), avec pour seule référence un fichier structure vide .


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
4. Configurez les variables d'environnement en copiant `.env.example` vers `.env` et en renseignant vos valeurs.
5. Lancez le serveur de développement Uvicorn :
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
3. Assurez-vous que l'application pointe sur l'API (vérifier `config.py` ou `.env`).
4. Lancez le serveur Flask :
   ```bash
   python app.py
   ```
   Le portail est accessible sur `http://localhost:5000/EDE/login`.

---

## Fonctionnalités par Rôle

### 1. Administrateur
Responsable du système avec des droits étendus :
- Gestion des Utilisateurs : Création, activation/suspension et réinitialisation des mots de passe.
- Gestion Pédagogique : Création des classes, des matières et affectations (Interventions prof → matière → classe).
- Statistiques et Tableaux de bord : Vision d'ensemble, taux de réussite global, moyenne générale.
- Résultats officiels : Sauvegarde et consultation du classement final par classe.

### 2. Professeur
Responsable pédagogique et de l'évaluation :
- Affectations : Visualisation des classes et matières qui lui sont assignées.
- Gestion des Notes : Saisie individuelle, modification et suppression des évaluations.
- Classement provisoire : Consultation du classement non-officiel de ses classes.

### 3. Étudiant
Utilisateur de la plateforme pour le suivi scolaire :
- Tableau de Bord : Synthèse des informations académiques (moyenne générale pondérée, rang, décision).
- Bulletin Détaillé : Rapport complet par matière incluant coefficients et classements partiels.
- Rang Officiel : Position de l'étudiant au sein de sa classe.

---

## Tests

Les tests automatisés de l'API sont situés dans le dossier `tests/`. Ils utilisent une base SQLite en mémoire, sans dépendance à l'infrastructure de production.

```bash
# Depuis la racine du projet
pip install -r requirement-test.txt
pytest tests/ -v
```
