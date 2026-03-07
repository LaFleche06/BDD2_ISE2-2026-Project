"""
Tests — Admin : Classes & Matières

Routes testées :
    GET    /admin/classes
    POST   /admin/classes
    PUT    /admin/classes/{id}
    DELETE /admin/classes/{id}
    GET    /admin/matieres
    POST   /admin/matieres
    PUT    /admin/matieres/{id}
    DELETE /admin/matieres/{id}

Cas couverts par section :

    Sécurité (partagée) :
        ✅ Sans token → 401
        ✅ Avec token d'un étudiant → 403

    Classes :
        ✅ Liste vide au départ
        ✅ Création valide (avec et sans annee_scolaire)
        ✅ Champ obligatoire manquant → 422
        ✅ Modification partielle (libellé seul)
        ✅ Modification sur id inexistant → 404
        ✅ Suppression → 204, puis liste vide
        ✅ Suppression id inexistant → 404

    Matières :
        ✅ Liste vide au départ
        ✅ Création valide avec coefficient personnalisé
        ✅ Coefficient par défaut à 1.00
        ✅ Modification du coefficient seul
        ✅ Suppression valide
        ✅ Suppression id inexistant → 404
"""

import pytest
from decimal import Decimal
from models.models import Utilisateur
from core.security import hash_password


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _post_classe(client, headers, libelle="Terminale A", annee="2024-2025"):
    """Crée une classe via l'API et retourne son JSON."""
    r = client.post("/admin/classes", json={
        "libelle": libelle,
        "annee_scolaire": annee,
    }, headers=headers)
    assert r.status_code == 201, f"Échec création classe : {r.json()}"
    return r.json()


def _post_matiere(client, headers, nom="Mathématiques", coefficient="2.00"):
    """Crée une matière via l'API et retourne son JSON."""
    r = client.post("/admin/matieres", json={
        "nom": nom,
        "coefficient": coefficient,
    }, headers=headers)
    assert r.status_code == 201, f"Échec création matière : {r.json()}"
    return r.json()


def _token_etudiant(client, db):
    """Crée un compte étudiant et retourne son token JWT."""
    user = Utilisateur(
        email="etu@test.com",
        mot_de_passe=hash_password("pass1234"),
        role="etudiant",
        actif=True,
    )
    db.add(user)
    db.commit()
    r = client.post("/auth/login", json={
        "email": "etu@test.com",
        "mot_de_passe": "pass1234",
    })
    return r.json()["access_token"]


# ─────────────────────────────────────────────
# SÉCURITÉ
# ─────────────────────────────────────────────

class TestSecurite:
    """Vérifie que les routes admin rejettent les requêtes non autorisées."""

    def test_sans_token(self, client):
        assert client.get("/admin/classes").status_code == 401
        assert client.post("/admin/classes", json={}).status_code == 401
        assert client.get("/admin/matieres").status_code == 401

    def test_role_insuffisant(self, client, db):
        """Un étudiant ne peut pas accéder aux routes admin → 403."""
        token = _token_etudiant(client, db)
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/admin/classes", headers=headers).status_code == 403
        assert client.get("/admin/matieres", headers=headers).status_code == 403


# ─────────────────────────────────────────────
# CLASSES
# ─────────────────────────────────────────────

class TestClasses:

    def test_liste_vide(self, client, headers_admin):
        r = client.get("/admin/classes", headers=headers_admin)
        assert r.status_code == 200
        assert r.json() == []

    def test_creation_valide(self, client, headers_admin):
        r = client.post("/admin/classes", json={
            "libelle": "Première S",
            "annee_scolaire": "2024-2025",
        }, headers=headers_admin)

        assert r.status_code == 201
        data = r.json()
        assert data["libelle"] == "Première S"
        assert data["annee_scolaire"] == "2024-2025"
        assert isinstance(data["id"], int)

    def test_creation_sans_annee(self, client, headers_admin):
        """annee_scolaire est optionnel → la création doit réussir."""
        r = client.post("/admin/classes", json={
            "libelle": "Seconde B",
        }, headers=headers_admin)
        assert r.status_code == 201
        assert r.json()["annee_scolaire"] is None

    def test_creation_sans_libelle(self, client, headers_admin):
        """libelle est obligatoire → 422."""
        r = client.post("/admin/classes", json={
            "annee_scolaire": "2024-2025",
        }, headers=headers_admin)
        assert r.status_code == 422

    def test_liste_apres_creation(self, client, headers_admin):
        _post_classe(client, headers_admin, "Term A")
        _post_classe(client, headers_admin, "Term B")

        r = client.get("/admin/classes", headers=headers_admin)
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_modification_partielle(self, client, headers_admin):
        """PUT ne doit modifier que les champs envoyés."""
        classe = _post_classe(client, headers_admin)
        cid = classe["id"]

        r = client.put(f"/admin/classes/{cid}", json={
            "libelle": "Terminale B",
        }, headers=headers_admin)

        assert r.status_code == 200
        data = r.json()
        assert data["libelle"] == "Terminale B"
        assert data["annee_scolaire"] == "2024-2025"  # inchangée

    def test_modification_id_inexistant(self, client, headers_admin):
        r = client.put("/admin/classes/9999", json={
            "libelle": "Fantôme",
        }, headers=headers_admin)
        assert r.status_code == 404

    def test_suppression(self, client, headers_admin):
        classe = _post_classe(client, headers_admin)
        cid = classe["id"]

        r = client.delete(f"/admin/classes/{cid}", headers=headers_admin)
        assert r.status_code == 204

        # Vérification : la liste est redevenue vide
        liste = client.get("/admin/classes", headers=headers_admin).json()
        assert liste == []

    def test_suppression_id_inexistant(self, client, headers_admin):
        r = client.delete("/admin/classes/9999", headers=headers_admin)
        assert r.status_code == 404


# ─────────────────────────────────────────────
# MATIÈRES
# ─────────────────────────────────────────────

class TestMatieres:

    def test_liste_vide(self, client, headers_admin):
        r = client.get("/admin/matieres", headers=headers_admin)
        assert r.status_code == 200
        assert r.json() == []

    def test_creation_valide(self, client, headers_admin):
        r = client.post("/admin/matieres", json={
            "nom": "Physique-Chimie",
            "coefficient": "1.50",
            "volume_horaire": "3h",
        }, headers=headers_admin)

        assert r.status_code == 201
        data = r.json()
        assert data["nom"] == "Physique-Chimie"
        assert Decimal(data["coefficient"]) == Decimal("1.50")
        assert data["volume_horaire"] == "3h"

    def test_coefficient_par_defaut(self, client, headers_admin):
        """Sans coefficient spécifié, la valeur par défaut est 1.00."""
        r = client.post("/admin/matieres", json={
            "nom": "Histoire",
        }, headers=headers_admin)
        assert r.status_code == 201
        assert Decimal(r.json()["coefficient"]) == Decimal("1.00")

    def test_modification_coefficient(self, client, headers_admin):
        matiere = _post_matiere(client, headers_admin)
        mid = matiere["id"]

        r = client.put(f"/admin/matieres/{mid}", json={
            "coefficient": "3.00",
        }, headers=headers_admin)

        assert r.status_code == 200
        assert Decimal(r.json()["coefficient"]) == Decimal("3.00")
        assert r.json()["nom"] == "Mathématiques"  # inchangé

    def test_suppression(self, client, headers_admin):
        matiere = _post_matiere(client, headers_admin)
        mid = matiere["id"]

        r = client.delete(f"/admin/matieres/{mid}", headers=headers_admin)
        assert r.status_code == 204

        liste = client.get("/admin/matieres", headers=headers_admin).json()
        assert liste == []

    def test_suppression_id_inexistant(self, client, headers_admin):
        r = client.delete("/admin/matieres/9999", headers=headers_admin)
        assert r.status_code == 404