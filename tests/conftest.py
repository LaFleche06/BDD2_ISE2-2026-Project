"""
conftest.py — Configuration globale des tests pytest


Arborescence attendue :
    projet/
    ├── API/      ← main.py, routers/, models/, core/, database/
    ├── tests/    ← ce dossier
    └── pytest.ini
"""

import os
import sys

# ── 1. Variables d'environnement AVANT tout import de l'app ──────────────────
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "cle-secrete-pour-tests-pytest-uniquement")

# ── 2. Rend API/ importable ───────────────────────────────────────────────────
API_DIR = os.path.join(os.path.dirname(__file__), "..", "API")
sys.path.insert(0, os.path.abspath(API_DIR))

# ── 3. Imports (après injection des env vars) ─────────────────────────────────
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database.session import get_db, Base
from core.security import hash_password
from models.models import Utilisateur, Classe, Matiere

# ── 4. Moteur SQLite avec StaticPool + FK enforcement ────────────────────────
engine_test = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine_test, "connect")
def activer_foreign_keys(dbapi_connection, connection_record):
    """
    Active les contraintes de clé étrangère à chaque connexion SQLite.
    Sans ce pragma, SQLite accepte n'importe quelle valeur de FK,
    ce qui rend les tests de contraintes inutiles.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSession = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine_test,
)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# ── 5. Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_db():
    """
    Crée toutes les tables avant chaque test, les supprime après.
    Isolation totale garantie : chaque test démarre avec une base propre.
    """
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture()
def db():
    """Session directe pour préparer/inspecter des données sans passer par l'API."""
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    """Client HTTP FastAPI — équivalent automatisé de Postman."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ── 6. Fixtures métier ────────────────────────────────────────────────────────

@pytest.fixture()
def admin_en_base(db):
    user = Utilisateur(
        email="admin@test.com",
        mot_de_passe=hash_password("Admin1234!"),
        role="admin",
        actif=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def token_admin(client, admin_en_base):
    r = client.post("/auth/login", json={
        "email": "admin@test.com",
        "mot_de_passe": "Admin1234!",
    })
    assert r.status_code == 200, f"Échec login admin (fixture) : {r.json()}"
    return r.json()["access_token"]


@pytest.fixture()
def headers_admin(token_admin):
    return {"Authorization": f"Bearer {token_admin}"}


@pytest.fixture()
def classe_en_base(db):
    obj = Classe(libelle="Terminale A", annee_scolaire="2024-2025")
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@pytest.fixture()
def matiere_en_base(db):
    from decimal import Decimal
    obj = Matiere(nom="Mathématiques", coefficient=Decimal("2.00"), volume_horaire="4h")
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj