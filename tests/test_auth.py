"""
Tests — POST /auth/login

Cas couverts :
    ✅ Credentials valides            → 200 + token JWT + rôle correct
    ✅ Mauvais mot de passe           → 401
    ✅ Email inconnu                  → 401 (même message que mauvais mdp)
    ✅ Compte désactivé               → 403
    ✅ Email au mauvais format        → 422 (rejeté par Pydantic)
    ✅ Body vide                      → 422
    ✅ Token retourné est utilisable  → accès à une route protégée
"""

import pytest
from models.models import Utilisateur
from core.security import hash_password


def _creer_utilisateur(db, email, role, actif=True):
    """Helper : insère un utilisateur en base directement."""
    user = Utilisateur(
        email=email,
        mot_de_passe=hash_password("pass1234"),
        role=role,
        actif=actif,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestLogin:

    def test_login_admin_succes(self, client, admin_en_base):
        """Un admin avec les bons credentials obtient un token valide."""
        r = client.post("/auth/login", json={
            "email": "admin@test.com",
            "mot_de_passe": "Admin1234!",
        })

        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "admin"
        # Le token est une chaîne non vide de plus de 20 caractères
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 20

    def test_token_est_utilisable(self, client, admin_en_base):
        """Le token obtenu permet d'accéder à une route protégée."""
        r_login = client.post("/auth/login", json={
            "email": "admin@test.com",
            "mot_de_passe": "Admin1234!",
        })
        token = r_login.json()["access_token"]

        # /admin/classes est une route admin protégée par JWT
        r = client.get(
            "/admin/classes",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200

    def test_mauvais_mot_de_passe(self, client, admin_en_base):
        """Un mauvais mot de passe → 401, même message que email inconnu."""
        r = client.post("/auth/login", json={
            "email": "admin@test.com",
            "mot_de_passe": "mauvais_mdp",
        })
        assert r.status_code == 401
        # Le message ne doit pas indiquer si c'est l'email ou le mot de passe
        # qui est faux (sécurité : pas d'énumération des comptes)
        assert "incorrect" in r.json()["detail"].lower()

    def test_email_inconnu(self, client):
        """Un email qui n'existe pas → 401 (même message que mauvais mdp)."""
        r = client.post("/auth/login", json={
            "email": "fantome@test.com",
            "mot_de_passe": "pass1234",
        })
        assert r.status_code == 401
        assert "incorrect" in r.json()["detail"].lower()

    def test_compte_desactive(self, client, db):
        """Un compte avec actif=False → 403 même avec le bon mot de passe."""
        _creer_utilisateur(db, "inactif@test.com", "etudiant", actif=False)

        r = client.post("/auth/login", json={
            "email": "inactif@test.com",
            "mot_de_passe": "pass1234",
        })
        assert r.status_code == 403
        assert "désactivé" in r.json()["detail"].lower()

    def test_email_format_invalide(self, client):
        """Un email mal formé est rejeté par Pydantic avant même d'atteindre la BDD."""
        r = client.post("/auth/login", json={
            "email": "pas-un-email",
            "mot_de_passe": "pass1234",
        })
        assert r.status_code == 422

    def test_body_vide(self, client):
        """Un body vide → 422 (champs requis manquants)."""
        r = client.post("/auth/login", json={})
        assert r.status_code == 422

    def test_roles_differents_retournes(self, client, db):
        """Le champ 'role' dans la réponse reflète bien le rôle du compte."""
        _creer_utilisateur(db, "prof@test.com", "prof")

        r = client.post("/auth/login", json={
            "email": "prof@test.com",
            "mot_de_passe": "pass1234",
        })
        assert r.status_code == 200
        assert r.json()["role"] == "prof"