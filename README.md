# 🎓 EDE — Espace de Gestion des Étudiants

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![SQL Server](https://img.shields.io/badge/SQL%20Server-2019%2B-red?logo=microsoftsqlserver)
![License](https://img.shields.io/badge/License-MIT-green)

> Application web de gestion scolaire développée avec **Flask** et **SQL Server**.  
> Elle permet la gestion complète des étudiants, professeurs, notes et résultats avec trois niveaux d'accès distincts.

---

## 📋 Table des matières

- [Aperçu](#-aperçu)
- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Structure du projet](#-structure-du-projet)
- [Base de données](#-base-de-données)
- [Comptes de test](#-comptes-de-test)
- [Technologies utilisées](#-technologies-utilisées)

---

## 👁️ Aperçu

EDE est une plateforme scolaire à trois rôles :

| Rôle | Accès |
|------|-------|
| 🎓 **Étudiant** | Consulter ses notes, sa moyenne pondérée et son rang |
| 📚 **Professeur** | Saisir, modifier et supprimer les notes de ses classes |
| ⚙️ **Administrateur** | Gérer toutes les données + classements + résultats officiels |

---

## ✨ Fonctionnalités

### 🎓 Espace Étudiant
- Tableau de bord avec moyenne générale, rang et situation (Admis/Ajourné)
- Consultation des notes par matière avec coefficient et barre visuelle
- Profil personnel (matricule, classe, année scolaire)

### 📚 Espace Professeur
- Saisie des notes par classe et par matière
- Modification et suppression des notes
- Visualisation des moyennes et classement par classe
- Vue de ses affectations (matière → classe)

### ⚙️ Espace Administrateur
- **Étudiants** : Ajouter, modifier, supprimer
- **Professeurs** : Ajouter, modifier, supprimer, affecter aux matières/classes
- **Matières** : Gestion complète avec coefficient et volume horaire
- **Classes** : Gestion complète avec année scolaire
- **Notes** : Vue globale avec filtrage par classe, ajout/modification/suppression
- **Classements** : Classement automatique par classe avec sauvegarde officielle des résultats
- **Statistiques globales** : Tableau de bord avec compteurs et moyenne générale

### 🔐 Authentification
- Connexion sécurisée avec hachage bcrypt
- Sessions Flask avec rôles distincts
- Déconnexion propre avec redirection vers la page de connexion

---

## 🏗️ Architecture

```
EDE/
├── app.py               # Routes Flask (toute la logique web)
├── db.py                # Couche d'accès aux données (CRUD)
├── config.py            # Paramètres de connexion SQL Server
├── setup_passwords.py   # Script de hachage des mots de passe (1 fois)
├── requirements.txt     # Dépendances Python
├── create_db.sql        # Script SQL complet (tables + vues + données test)
└── templates/
    ├── base.html        # Layout principal (sidebar + topbar)
    ├── login.html       # Page de connexion
    ├── index.html       # Page d'accueil
    ├── test_db.html     # Test de connexion BD
    ├── etudiant/
    │   ├── dashboard.html
    │   ├── notes.html
    │   └── profil.html
    ├── prof/
    │   ├── dashboard.html
    │   ├── notes.html
    │   ├── moyennes.html
    │   └── classe.html
    └── admin/
        ├── dashboard.html
        ├── etudiants.html
        ├── form_etudiant.html
        ├── professeurs.html
        ├── form_prof.html
        ├── matieres.html
        ├── form_matiere.html
        ├── classes.html
        ├── notes.html
        └── classements.html
```

---

## ⚙️ Prérequis

- **Python 3.12** (ne pas utiliser 3.13 ou 3.14 — pyodbc non compatible)
- **SQL Server** (Express, Developer ou Standard) + **SSMS**
- **ODBC Driver 17 for SQL Server**
- **pip**

---

## 🚀 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-utilisateur/ede-gestion-etudiants.git
cd ede-gestion-etudiants
```

### 2. Créer un environnement virtuel Python 3.12

```powershell
py -3.12 -m venv venv312
venv312\Scripts\activate
```

### 3. Installer les dépendances

```powershell
pip install flask pyodbc bcrypt
```

### 4. Créer la base de données

Ouvrez **SSMS**, puis :
- `Fichier` → `Ouvrir` → `Fichier` → sélectionnez `create_db.sql`
- Appuyez sur **F5**

Vous devez voir :
```
Base EtudiantDB creee avec succes!
Etape suivante : python setup_passwords.py
```

### 5. Configurer la connexion

Modifiez `config.py` avec vos paramètres SQL Server :

```python
DB_SERVER   = 'localhost\\SQLEXPRESS'  # Votre serveur
DB_NAME     = 'EtudiantDB'
DB_USER     = 'sa'
DB_PASSWORD = 'VotreMotDePasse'
```

Ou utilisez l'**authentification Windows** (plus simple) :

```python
def get_conn_string():
    return (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"Trusted_Connection=yes;"
        f"TrustServerCertificate=yes;"
    )
```

### 6. Hacher les mots de passe

```powershell
python setup_passwords.py
```

Résultat attendu :
```
[OK] admin@ede.ca
[OK] dupont@ede.ca
[OK] alice@ede.ca
...
8/8 mots de passe mis a jour.
```

### 7. Lancer l'application

```powershell
python app.py
```

Ouvrez votre navigateur sur :
```
http://localhost:5000/EDE/index
```

---

## 🗄️ Base de données

### Tables (9)

| Table | Description |
|-------|-------------|
| `UTILISATEUR` | Comptes de connexion (email, mot de passe, rôle) |
| `ETUDIANT` | Informations des étudiants (matricule, classe, téléphone) |
| `PROFESSEUR` | Informations des professeurs |
| `ADMINISTRATEUR` | Informations des administrateurs |
| `Classe` | Classes (libellé, année scolaire) |
| `MATIERES` | Matières (coefficient, volume horaire) |
| `INTERVIENT` | Affectations prof → matière → classe |
| `NOTES` | Notes des étudiants (valeur, date de saisie) |
| `RESULTAT` | Résultats officiels sauvegardés |

### Vues SQL (7)

| Vue | Description |
|-----|-------------|
| `VUE_NOTES_COMPLETES` | Notes avec tous les détails (étudiant, prof, matière, classe) |
| `VUE_MOYENNES_ETUDIANTS` | Moyennes pondérées par étudiant + décision |
| `VUE_CLASSEMENT_CLASSE` | Classement automatique avec `RANK()` par classe |
| `VUE_STATS_CLASSE` | Statistiques agrégées par classe (admis, taux réussite…) |
| `VUE_ENSEIGNEMENTS` | Tableau des affectations professeurs |
| `VUE_RESULTATS_COMPLETS` | Résultats officiels enrichis |
| `VUE_STATS_GLOBALES` | Compteurs globaux du système |

---

## 🔑 Comptes de test

| Rôle | Email | Mot de passe |
|------|-------|--------------|
| ⚙️ Administrateur | `admin@ede.ca` | `admin123` |
| 📚 Professeur | `dupont@ede.ca` | `prof123` |
| 📚 Professeur | `martin@ede.ca` | `prof123` |
| 📚 Professeur | `leblanc@ede.ca` | `prof123` |
| 🎓 Étudiant | `alice@ede.ca` | `etudiant123` |
| 🎓 Étudiant | `marc@ede.ca` | `etudiant123` |
| 🎓 Étudiant | `sophie@ede.ca` | `etudiant123` |
| 🎓 Étudiant | `karim@ede.ca` | `etudiant123` |

---

## 🛠️ Technologies utilisées

| Technologie | Version | Rôle |
|-------------|---------|------|
| Python | 3.12 | Langage principal |
| Flask | 3.0 | Framework web |
| pyodbc | 5.0 | Connexion SQL Server |
| bcrypt | 4.1 | Hachage des mots de passe |
| SQL Server | 2019+ | Base de données |
| Jinja2 | 3.x | Moteur de templates HTML |
| HTML/CSS | — | Interface utilisateur |

---

## 📄 Licence

Ce projet est sous licence **MIT** — libre d'utilisation, modification et distribution.

---


