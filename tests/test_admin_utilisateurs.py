"""
Tests — Admin : Étudiants, Professeurs & Interventions

Correctifs v2
─────────────
1. DELETE /admin/interventions avec body JSON :
   TestClient.delete() n'accepte pas json= (limitation starlette).
   On utilise client.request("DELETE", url, json=...) à la place.

2. test_creation_classe_inexistante :
   Nécessite PRAGMA foreign_keys=ON dans conftest.py (déjà fait).
   Sans ce pragma SQLite acceptait la FK invalide → ResponseValidationError 500.
   Avec le pragma → IntegrityError → le router renvoie 400. ✅
"""

import json as json_lib
import pytest
from models.models import Utilisateur
from core.security import hash_password


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _post_classe(client, headers, libelle="Term A"):
    r = client.post("/admin/classes", json={
        "libelle": libelle, "annee_scolaire": "2024-2025",
    }, headers=headers)
    assert r.status_code == 201
    return r.json()


def _post_matiere(client, headers, nom="Maths"):
    r = client.post("/admin/matieres", json={
        "nom": nom, "coefficient": "2.00",
    }, headers=headers)
    assert r.status_code == 201
    return r.json()


def _post_etudiant(client, headers, classe_id, email="etu@test.com"):
    r = client.post("/admin/etudiants", json={
        "nom": "Diallo", "prenom": "Amara",
        "email": email, "mot_de_passe": "pass1234",
        "classe_id": classe_id,
    }, headers=headers)
    assert r.status_code == 201, f"Échec création étudiant : {r.json()}"
    return r.json()


def _post_professeur(client, headers, email="prof@test.com"):
    r = client.post("/admin/professeurs", json={
        "nom": "Dupont", "prenom": "Jean",
        "email": email, "mot_de_passe": "pass1234",
    }, headers=headers)
    assert r.status_code == 201, f"Échec création professeur : {r.json()}"
    return r.json()


def _delete_with_body(client, url, payload, headers):
    """
    Wrapper pour DELETE avec body JSON.
    TestClient.delete() n'accepte pas json= (héritage requests).
    client.request() le supporte via httpx.
    """
    return client.request("DELETE", url, json=payload, headers=headers)


# ─────────────────────────────────────────────
# ÉTUDIANTS
# ─────────────────────────────────────────────

class TestEtudiants:

    def test_creation_valide(self, client, headers_admin, db):
        """Créer un étudiant crée aussi son compte Utilisateur avec rôle 'etudiant'."""
        classe = _post_classe(client, headers_admin)
        etu = _post_etudiant(client, headers_admin, classe["id"])

        assert etu["nom"]    == "Diallo"
        assert etu["prenom"] == "Amara"
        assert isinstance(etu["matricule"], int)

        user = db.query(Utilisateur).filter(Utilisateur.id == etu["utilisateur_id"]).first()
        assert user is not None
        assert user.role  == "etudiant"
        assert user.email == "etu@test.com"
        assert user.actif is True

    def test_creation_email_duplique(self, client, headers_admin):
        """Deux étudiants avec le même email → 400 au second."""
        classe = _post_classe(client, headers_admin)
        _post_etudiant(client, headers_admin, classe["id"], "etu@test.com")

        r = client.post("/admin/etudiants", json={
            "nom": "Autre", "prenom": "Prénom",
            "email": "etu@test.com",   # email déjà pris
            "mot_de_passe": "pass1234",
            "classe_id": classe["id"],
        }, headers=headers_admin)
        assert r.status_code == 400
        assert "déjà utilisé" in r.json()["detail"]

    def test_creation_classe_inexistante(self, client, headers_admin):
        """
        Référencer une classe qui n'existe pas → 400.
        Nécessite PRAGMA foreign_keys=ON dans conftest (déjà activé).
        """
        r = client.post("/admin/etudiants", json={
            "nom": "Test", "prenom": "Test",
            "email": "test@test.com", "mot_de_passe": "pass1234",
            "classe_id": 9999,
        }, headers=headers_admin)
        assert r.status_code == 400

    def test_liste(self, client, headers_admin):
        classe = _post_classe(client, headers_admin)
        _post_etudiant(client, headers_admin, classe["id"], "etu1@test.com")
        _post_etudiant(client, headers_admin, classe["id"], "etu2@test.com")

        r = client.get("/admin/etudiants", headers=headers_admin)
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_get_par_matricule(self, client, headers_admin):
        classe = _post_classe(client, headers_admin)
        etu = _post_etudiant(client, headers_admin, classe["id"])

        r = client.get(f"/admin/etudiants/{etu['matricule']}", headers=headers_admin)
        assert r.status_code == 200
        assert r.json()["matricule"] == etu["matricule"]

    def test_get_matricule_inexistant(self, client, headers_admin):
        assert client.get("/admin/etudiants/9999", headers=headers_admin).status_code == 404

    def test_modification_partielle(self, client, headers_admin):
        """PUT ne doit modifier que les champs envoyés."""
        classe = _post_classe(client, headers_admin)
        etu = _post_etudiant(client, headers_admin, classe["id"])

        r = client.put(f"/admin/etudiants/{etu['matricule']}", json={
            "nom": "Diallo-Modifié",
        }, headers=headers_admin)
        assert r.status_code == 200
        assert r.json()["nom"]    == "Diallo-Modifié"
        assert r.json()["prenom"] == "Amara"            # inchangé

    def test_suppression_cascade_utilisateur(self, client, headers_admin, db):
        """Supprimer un étudiant supprime aussi son compte Utilisateur."""
        classe = _post_classe(client, headers_admin)
        etu = _post_etudiant(client, headers_admin, classe["id"])
        utilisateur_id = etu["utilisateur_id"]

        r = client.delete(f"/admin/etudiants/{etu['matricule']}", headers=headers_admin)
        assert r.status_code == 204

        user = db.query(Utilisateur).filter(Utilisateur.id == utilisateur_id).first()
        assert user is None

    def test_suppression_matricule_inexistant(self, client, headers_admin):
        assert client.delete("/admin/etudiants/9999", headers=headers_admin).status_code == 404


# ─────────────────────────────────────────────
# PROFESSEURS
# ─────────────────────────────────────────────

class TestProfesseurs:

    def test_creation_valide(self, client, headers_admin, db):
        prof = _post_professeur(client, headers_admin)

        assert prof["nom"]    == "Dupont"
        assert prof["prenom"] == "Jean"

        user = db.query(Utilisateur).filter(Utilisateur.id == prof["utilisateur_id"]).first()
        assert user is not None
        assert user.role == "prof"

    def test_creation_email_duplique(self, client, headers_admin):
        _post_professeur(client, headers_admin, "prof@test.com")
        r = client.post("/admin/professeurs", json={
            "nom": "Autre", "prenom": "Prof",
            "email": "prof@test.com",
            "mot_de_passe": "pass1234",
        }, headers=headers_admin)
        assert r.status_code == 400

    def test_liste(self, client, headers_admin):
        _post_professeur(client, headers_admin, "prof1@test.com")
        _post_professeur(client, headers_admin, "prof2@test.com")

        r = client.get("/admin/professeurs", headers=headers_admin)
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_get_par_id(self, client, headers_admin):
        prof = _post_professeur(client, headers_admin)
        r = client.get(f"/admin/professeurs/{prof['id']}", headers=headers_admin)
        assert r.status_code == 200
        assert r.json()["id"] == prof["id"]

    def test_modification_telephone(self, client, headers_admin):
        prof = _post_professeur(client, headers_admin)
        r = client.put(f"/admin/professeurs/{prof['id']}", json={
            "telephone": "0612345678",
        }, headers=headers_admin)
        assert r.status_code == 200
        assert r.json()["telephone"] == "0612345678"
        assert r.json()["nom"]       == "Dupont"   # inchangé

    def test_suppression_cascade_utilisateur(self, client, headers_admin, db):
        prof = _post_professeur(client, headers_admin)
        utilisateur_id = prof["utilisateur_id"]

        r = client.delete(f"/admin/professeurs/{prof['id']}", headers=headers_admin)
        assert r.status_code == 204

        user = db.query(Utilisateur).filter(Utilisateur.id == utilisateur_id).first()
        assert user is None

    def test_suppression_id_inexistant(self, client, headers_admin):
        assert client.delete("/admin/professeurs/9999", headers=headers_admin).status_code == 404


# ─────────────────────────────────────────────
# INTERVENTIONS
# ─────────────────────────────────────────────

class TestInterventions:

    def _setup(self, client, headers):
        return (
            _post_professeur(client, headers),
            _post_matiere(client, headers),
            _post_classe(client, headers),
        )

    def _payload(self, prof, matiere, classe):
        return {
            "professeur_id": prof["id"],
            "matiere_id":    matiere["id"],
            "classe_id":     classe["id"],
        }

    def test_creation_valide(self, client, headers_admin):
        prof, matiere, classe = self._setup(client, headers_admin)
        payload = self._payload(prof, matiere, classe)

        r = client.post("/admin/interventions", json=payload, headers=headers_admin)
        assert r.status_code == 201

        data = r.json()
        assert data["professeur_id"] == prof["id"]
        assert data["matiere_id"]    == matiere["id"]
        assert data["classe_id"]     == classe["id"]
        # Objets imbriqués présents dans la réponse
        assert data["professeur"]["nom"] == "Dupont"
        assert data["matiere"]["nom"]    == "Maths"

    def test_creation_doublon(self, client, headers_admin):
        prof, matiere, classe = self._setup(client, headers_admin)
        payload = self._payload(prof, matiere, classe)

        client.post("/admin/interventions", json=payload, headers=headers_admin)
        r = client.post("/admin/interventions", json=payload, headers=headers_admin)

        assert r.status_code == 400
        assert "existe déjà" in r.json()["detail"]

    def test_liste(self, client, headers_admin):
        prof, matiere, classe = self._setup(client, headers_admin)
        client.post("/admin/interventions",
                    json=self._payload(prof, matiere, classe),
                    headers=headers_admin)

        r = client.get("/admin/interventions", headers=headers_admin)
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_suppression(self, client, headers_admin):
        """
        DELETE /admin/interventions avec body JSON.
        Utilise client.request() car TestClient.delete() n'accepte pas json=.
        """
        prof, matiere, classe = self._setup(client, headers_admin)
        payload = self._payload(prof, matiere, classe)

        client.post("/admin/interventions", json=payload, headers=headers_admin)

        r = _delete_with_body(client, "/admin/interventions", payload, headers_admin)
        assert r.status_code == 204

        liste = client.get("/admin/interventions", headers=headers_admin).json()
        assert liste == []

    def test_suppression_inexistante(self, client, headers_admin):
        r = _delete_with_body(client, "/admin/interventions", {
            "professeur_id": 999, "matiere_id": 999, "classe_id": 999,
        }, headers_admin)
        assert r.status_code == 404