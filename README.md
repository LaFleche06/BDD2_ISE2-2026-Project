<div align="center">

# 🏛️ Campus ENSAE — EDE
### Système de Gestion Scolaire

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![SQL Server](https://img.shields.io/badge/SQL%20Server-AWS%20RDS-CC2927?style=for-the-badge&logo=microsoftsqlserver&logoColor=white)](https://aws.amazon.com/rds/)
[![Deployed on Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://campusensae.onrender.com/EDE/login)

**Plateforme complète de gestion de la scolarité — étudiants, professeurs, notes et classements.**  
Architecture moderne en deux couches : une **API REST FastAPI** et un **portail web Flask**.

[🌐 Accéder à l'application](https://campusensae.onrender.com/) · [📖 Documentation API](https://api-ensae-bdd2-ise2-2026.duckdns.org/docs) · [🐛 Signaler un bug](../../issues)

</div>

---

## 📸 Aperçu

| Portail Web (Flask) | API REST (Swagger UI) |
|:---:|:---:|
| ![Login](https://raw.githubusercontent.com/LaFleche06/BDD2_ISE2-2026-Project/main/docs/screenshot_login.png) | ![Swagger](https://raw.githubusercontent.com/LaFleche06/BDD2_ISE2-2026-Project/main/docs/screenshot_api.png) |

![Dashboard Admin](https://raw.githubusercontent.com/LaFleche06/BDD2_ISE2-2026-Project/main/docs/screenshot_dashboard.png)

---

## 📋 Table des matières

- [Architecture](#-architecture)
- [Fonctionnalités](#-fonctionnalités-par-rôle)
- [Infrastructure Cloud](#-infrastructure-cloud)
- [Lancer en local](#-lancer-en-local)
- [Tests](#-tests)
- [Comptes de démonstration](#-comptes-de-démonstration)
- [Stack technique](#-stack-technique)

---

## 🏗️ Architecture

Le projet est scindé en **deux couches indépendantes** qui communiquent par requêtes HTTP :

```
┌─────────────────────────────────────────────────────────────┐
│                        NAVIGATEUR                           │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           PORTAIL WEB  /Projet_BDD2                         │
│           Flask + Jinja2 — Render.com                       │
│           Server-Side Rendering                             │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/REST + JWT
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           API BACKEND  /API                                 │
│           FastAPI + SQLAlchemy — AWS EC2                    │
│           Authentification JWT · Swagger /docs              │
└───────────────────────────┬─────────────────────────────────┘
                            │ SQL
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           BASE DE DONNÉES                                   │
│           SQL Server — Amazon RDS (Free Tier)               │
└─────────────────────────────────────────────────────────────┘
```

### Structure du dépôt

```
campus-ensae-ede/
├── API/                        # Backend FastAPI
│   ├── main.py                 # Point d'entrée FastAPI
│   ├── models.py               # Modèles SQLAlchemy
│   ├── schemas.py              # Schémas Pydantic
│   ├── auth.py                 # Authentification JWT
│   ├── routes/                 # Endpoints par ressource
│   ├── requirements.txt
│   └── .env.example            # Template des variables d'environnement
│
├── Projet_BDD2/                # Frontend Flask
│   ├── app.py                  # Routes Flask
│   ├── config.py               # Configuration (lit depuis .env)
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── etudiant/
│   │   ├── prof/
│   │   └── admin/
│   └── requirements.txt
│
├── tests/                      # Tests automatisés (SQLite en mémoire)
├── docs/                       # Captures d'écran pour le README
└── README.md
```

---

## ✨ Fonctionnalités par rôle

<details>
<summary><b>⚙️ Administrateur</b> — Droits étendus sur l'ensemble du système</summary>

<br>

- **Gestion des utilisateurs** — Création, activation/suspension, réinitialisation des mots de passe
- **Gestion pédagogique** — Création des classes, matières et affectations (prof → matière → classe)
- **Statistiques globales** — Taux de réussite, moyennes, compteurs en temps réel
- **Résultats officiels** — Sauvegarde et consultation du classement final par classe

</details>

<details>
<summary><b>📚 Professeur</b> — Gestion pédagogique et évaluation</summary>

<br>

- **Affectations** — Visualisation des classes et matières assignées
- **Gestion des notes** — Saisie individuelle, modification et suppression
- **Classement provisoire** — Consultation du classement non-officiel de ses classes

</details>

<details>
<summary><b>🎓 Étudiant</b> — Suivi de son parcours scolaire</summary>

<br>

- **Tableau de bord** — Moyenne générale pondérée, rang, décision (Admis/Ajourné)
- **Bulletin détaillé** — Rapport complet par matière avec coefficients
- **Rang officiel** — Position dans la classe après validation administrative

</details>

---

## ☁️ Infrastructure Cloud

### 1. Base de données — Amazon RDS for SQL Server

> Service **PaaS** : AWS gère l'installation, les sauvegardes et les mises à jour automatiquement.

| Paramètre | Valeur |
|-----------|--------|
| Moteur | SQL Server Express Edition |
| Stockage | 20 Gio SSD |
| Accès | Public (authentification SQL Server) |
| Migration | Script SQL complet généré via SSMS |

### 2. API Backend — FastAPI sur Amazon EC2

L'API est l'unique point d'entrée vers la base de données. Elle assure :
- 🔐 **Authentification JWT** — Tokens sécurisés pour chaque session
- 📄 **Documentation Swagger** — Auto-générée via OpenAPI sur `/docs`
- 🔄 **Supervision Systemd** — Redémarrage automatique en cas de défaillance
- 🔀 **Reverse Proxy Nginx** — Ports 80/443 redirigés vers le processus local
- 🔒 **SSL/TLS Let's Encrypt** — HTTPS activé via Certbot

**Déploiement d'une mise à jour :**
```bash
git pull && sudo systemctl restart api-ede
```

### 3. Portail Web — Flask sur Render.com

| Fonctionnalité | Détail |
|----------------|--------|
| Déploiement | Automatique via webhook GitHub (branche `main`) |
| Variables sensibles | Stockées dans Render.com, jamais poussées sur Git |
| URL publique | [campusensae.onrender.com](https://campusensae.onrender.com/) |

### 4. Organisation Git

```
main              ← code production stable
└── feature/xxx   ← branches de développement → merge vers main
```

> 🔒 Les secrets (clés JWT, URLs RDS, mots de passe) sont dans `.env` (ignoré par `.gitignore`).  
> Un fichier `.env.example` sert de référence vide pour les collaborateurs.

---

## 💻 Lancer en local

### Prérequis

- Python **3.10+**
- SQL Server local **ou** URL de l'instance RDS
- [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/fr-fr/sql/connect/odbc/download-odbc-driver-for-sql-server)

---

### ① Lancer l'API FastAPI

```bash
# 1. Aller dans le dossier API
cd API

# 2. Créer et activer l'environnement virtuel
python -m venv env
env\Scripts\activate        # Windows
source env/bin/activate     # Linux/Mac

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# → Editer .env avec vos valeurs

# 5. Lancer le serveur
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

✅ API disponible sur `http://localhost:8000`  
✅ Documentation Swagger sur `http://localhost:8000/docs`

---

### ② Lancer le portail Flask

```bash
# 1. Aller dans le dossier web (nouveau terminal)
cd Projet_BDD2

# 2. Activer l'environnement virtuel
env\Scripts\activate

# 3. Installer les dépendances
pip install flask requests

# 4. Vérifier que config.py pointe sur l'API locale
# API_URL = "http://localhost:8000"

# 5. Lancer Flask
python app.py
```

✅ Portail disponible sur `http://localhost:5000/EDE/login`

---

## 🧪 Tests

Les tests de l'API utilisent une base **SQLite en mémoire** — aucune dépendance à l'infrastructure de production.

```bash
# Installer les dépendances de test
pip install -r requirement-test.txt

# Lancer les tests avec verbosité
pytest tests/ -v
```

---

## 🔑 Comptes de démonstration

| Rôle | Email | Mot de passe |
|------|-------|:------------:|
| ⚙️ Administrateur | `admin@ensae.sn` | `admin123` |
| 📚 Enseignant | `prof@ensae.sn` | `prof123` |
| 🎓 Étudiant | `etudiant@ensae.sn` | `etu123` |

> 🌐 Accessible directement sur [campusensae.onrender.com/EDE/login](https://campusensae.onrender.com/)

---

## 🛠️ Stack technique

| Couche | Technologie | Rôle |
|--------|-------------|------|
| **Backend API** | FastAPI + Uvicorn | API REST, logique métier, JWT |
| **ORM** | SQLAlchemy | Abstraction base de données |
| **Validation** | Pydantic | Schémas de données et validation |
| **Frontend** | Flask + Jinja2 | Rendu serveur, portail utilisateur |
| **Base de données** | SQL Server (RDS) | Stockage persistant |
| **Sécurité** | JWT + bcrypt | Authentification et hachage |
| **Hébergement API** | AWS EC2 + Nginx | Serveur de production |
| **Hébergement Web** | Render.com | Déploiement continu |
| **SSL** | Let's Encrypt | Certificats HTTPS |
| **CI/CD** | GitHub + Render Webhooks | Déploiement automatique |

---

<div align="center">

Développé dans le cadre du cours **Bases de Données 2** — ENSAE 2026 par :
* FOGWOUNG DJOUFACK Sarah-Laure
* ONANENA AMANA Jeanne De La Flèche
* DIEME Moussa
* ILLY Jacques
* SEUNKAM PAHANE Kerencia Dyvana,
  
Elèves ingénieurs statisticiens économistes

Sous la supervision de : 
**M. Saliou THIAW**,

Ingénieur informaticien

</div>
