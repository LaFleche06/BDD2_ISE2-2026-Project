"""
Point d'entrée de l'API — Gestion Scolaire

Routers :
    /auth           → authentification (login)
    /admin          → espace administrateur
    /prof           → espace professeur
    /etudiant       → espace étudiant
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.session import get_db, engine
from models.models import Base

from routers import auth
from routers.admin import admin_classes_matieres
from routers.admin import admin_utilisateurs
from routers.admin import admin_stats
from routers import professeur
from routers import etudiant

app = FastAPI(
    title="API Gestion Scolaire",
    description="""
## API REST — Gestion Scolaire

### Espaces disponibles

| Espace       | Rôle requis | Description                                     |
|--------------|-------------|-------------------------------------------------|
| `/auth`      | —           | Authentification JWT                            |
| `/admin`     | `admin`     | Gestion complète : classes, profs, étudiants... |
| `/prof`      | `prof`      | Saisie et consultation des notes                |
| `/etudiant`  | `etudiant`  | Dashboard et consultation des notes             |

### Authentification
Toutes les routes protégées nécessitent un token JWT dans le header :
```
Authorization: Bearer <token>
```
Obtenez un token via **POST /auth/login**.
    """,
    version="1.0.0",
)

# ── Tables ────────────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(admin_classes_matieres.router)
app.include_router(admin_utilisateurs.router)
app.include_router(admin_stats.router)
app.include_router(professeur.router)
app.include_router(etudiant.router)


# ── Endpoints utilitaires ─────────────────────────────────────────────────────

@app.get("/", tags=["Root"], summary="Health check")
def root():
    """Vérifie que l'API est bien démarrée."""
    return {
        "status": "ok",
        "message": "API Gestion Scolaire — voir /docs pour la documentation interactive",
    }


@app.get("/test-aws", tags=["Debug"], summary="Test connexion AWS RDS")
def test_connection(db: Session = Depends(get_db)):
    """
    Vérifie la connexion à la base de données AWS RDS.

    - Exécute `SELECT @@VERSION`
    - Retourne la version du serveur SQL si la connexion réussit
    - Retourne un message d'erreur en cas d'échec
    """
    try:
        result = db.execute(text("SELECT @@VERSION")).fetchone()
        if result is None:
            return {
                "status": "Error",
                "message": "Aucun résultat retourné",
            }
        return {
            "status": "Success",
            "message": "Connexion à AWS RDS réussie !",
            "sql_server_version": result[0],
        }
    except Exception as e:
        return {
            "status": "Error",
            "message": str(e),
        }