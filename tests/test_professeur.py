"""
Tests — Espace Professeur

Routes testées :
    GET    /prof/interventions
    GET    /prof/classes/{id}/etudiants
    GET    /prof/notes
    POST   /prof/notes
    PUT    /prof/notes/{id}
    DELETE /prof/notes/{id}
    GET    /prof/classes/{id}/moyennes

Cas couverts :

    Sécurité :
        ✅ Sans token → 401
        ✅ Avec token étudiant → 403
        ✅ Un prof ne voit que ses propres données

    Interventions :
        ✅ Liste ses affectations uniquement
        ✅ Liste vide si aucune affectation

    Étudiants d'une classe :
        ✅ Retourne les étudiants de sa classe
        ✅ Classe d'un autre prof → 403
        ✅ Triés par nom

    Notes :
        ✅ Saisie valide → 201
        ✅ Note hors plage [0-20] → 422
        ✅ Doublon étudiant/matière → 400
        ✅ Matière non affectée → 403
        ✅ Modification de sa propre note
        ✅ Modification de la note d'un autre prof → 403
        ✅ Suppression de sa propre note → 204
        ✅ Suppression note d'un autre prof → 403
        ✅ Note inexistante → 404

    Moyennes :
        ✅ Classement correct avec moyennes pondérées
        ✅ Classe non affectée → 403
        ✅ Classe sans notes → liste vide
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from models.models import (
    Utilisateur, Classe, Matiere, Etudiant,
    Professeur, Note, Intervention,
)
from core.security import hash_password


# ─────────────────────────────────────────────
# FIXTURE — contexte complet pour les tests prof
# ─────────────────────────────────────────────

@pytest.fixture()
def contexte_prof(db, client):
    """
    Crée et retourne un contexte complet :
        - 1 classe
        - 2 matières
        - 1 professeur principal (connecté dans les tests)
        - 1 second professeur (pour tester les accès croisés)
        - 2 étudiants
        - affectation prof principal → matière1 → classe
        - token JWT du professeur principal
    """
    # Classe
    classe = Classe(libelle="Term A", annee_scolaire="2024-2025")
    db.add(classe)
    db.flush()

    # Matières
    m1 = Matiere(nom="Maths",    coefficient=Decimal("2.00"))
    m2 = Matiere(nom="Histoire", coefficient=Decimal("1.00"))
    db.add_all([m1, m2])
    db.flush()

    # Prof principal
    u_p1 = Utilisateur(email="prof1@test.com", mot_de_passe=hash_password("pass1234"), role="prof", actif=True)
    db.add(u_p1)
    db.flush()
    prof1 = Professeur(utilisateur_id=u_p1.id, nom="Dupont", prenom="Jean")
    db.add(prof1)
    db.flush()

    # Second prof (pour les tests d'accès croisé)
    u_p2 = Utilisateur(email="prof2@test.com", mot_de_passe=hash_password("pass1234"), role="prof", actif=True)
    db.add(u_p2)
    db.flush()
    prof2 = Professeur(utilisateur_id=u_p2.id, nom="Martin", prenom="Paul")
    db.add(prof2)
    db.flush()

    # Étudiants
    u_a = Utilisateur(email="etua@test.com", mot_de_passe=hash_password("p"), role="etudiant", actif=True)
    db.add(u_a)
    db.flush()
    etu_a = Etudiant(utilisateur_id=u_a.id, classe_id=classe.id, nom="Alice", prenom="A")
    db.add(etu_a)
    db.flush()

    u_b = Utilisateur(email="etub@test.com", mot_de_passe=hash_password("p"), role="etudiant", actif=True)
    db.add(u_b)
    db.flush()
    etu_b = Etudiant(utilisateur_id=u_b.id, classe_id=classe.id, nom="Bob", prenom="B")
    db.add(etu_b)
    db.flush()

    # Affectation prof1 → m1 → classe  (pas m2, pour tester les refus)
    db.add(Intervention(professeur_id=prof1.id, matiere_id=m1.id, classe_id=classe.id))
    db.commit()

    # Token prof principal
    r = client.post("/auth/login", json={"email": "prof1@test.com", "mot_de_passe": "pass1234"})
    token = r.json()["access_token"]

    return {
        "classe": classe, "m1": m1, "m2": m2,
        "prof1": prof1, "prof2": prof2,
        "etu_a": etu_a, "etu_b": etu_b,
        "headers": {"Authorization": f"Bearer {token}"},
        "token_prof2": client.post("/auth/login", json={"email": "prof2@test.com", "mot_de_passe": "pass1234"}).json()["access_token"],
    }


# ─────────────────────────────────────────────
# SÉCURITÉ
# ─────────────────────────────────────────────

class TestProfSecurite:

    def test_sans_token(self, client):
        assert client.get("/prof/notes").status_code == 401
        assert client.get("/prof/interventions").status_code == 401

    def test_role_etudiant_refuse(self, client, db):
        u = Utilisateur(email="etu@test.com", mot_de_passe=hash_password("p"), role="etudiant", actif=True)
        db.add(u)
        db.commit()
        token = client.post("/auth/login", json={"email": "etu@test.com", "mot_de_passe": "p"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/prof/notes", headers=headers).status_code == 403


# ─────────────────────────────────────────────
# INTERVENTIONS
# ─────────────────────────────────────────────

class TestProfInterventions:

    def test_mes_interventions(self, client, contexte_prof):
        h = contexte_prof["headers"]
        r = client.get("/prof/interventions", headers=h)
        assert r.status_code == 200
        data = r.json()
        # prof1 a 1 seule affectation
        assert len(data) == 1
        assert data[0]["matiere"]["nom"] == "Maths"

    def test_aucune_intervention(self, client, db):
        """Un prof sans affectation reçoit une liste vide."""
        u = Utilisateur(email="prof_vide@test.com", mot_de_passe=hash_password("p"), role="prof", actif=True)
        db.add(u)
        db.flush()
        db.add(Professeur(utilisateur_id=u.id, nom="Vide", prenom="Prof"))
        db.commit()

        token = client.post("/auth/login", json={"email": "prof_vide@test.com", "mot_de_passe": "p"}).json()["access_token"]
        r = client.get("/prof/interventions", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json() == []


# ─────────────────────────────────────────────
# ÉTUDIANTS D'UNE CLASSE
# ─────────────────────────────────────────────

class TestProfEtudiantsClasse:

    def test_liste_etudiants_sa_classe(self, client, contexte_prof):
        h = contexte_prof["headers"]
        classe_id = contexte_prof["classe"].id

        r = client.get(f"/prof/classes/{classe_id}/etudiants", headers=h)
        assert r.status_code == 200
        assert len(r.json()) == 2
        # triés par nom
        noms = [e["nom"] for e in r.json()]
        assert noms == sorted(noms)

    def test_classe_non_affectee_refuse(self, client, db, contexte_prof):
        """Un prof ne peut pas voir les étudiants d'une classe qui n'est pas la sienne."""
        autre_classe = Classe(libelle="Autre", annee_scolaire="2024-2025")
        db.add(autre_classe)
        db.commit()
        db.refresh(autre_classe)

        h = contexte_prof["headers"]
        r = client.get(f"/prof/classes/{autre_classe.id}/etudiants", headers=h)
        assert r.status_code == 403


# ─────────────────────────────────────────────
# SAISIE DE NOTES
# ─────────────────────────────────────────────

class TestProfSaisieNote:

    def test_saisie_valide(self, client, contexte_prof):
        h   = contexte_prof["headers"]
        m1  = contexte_prof["m1"]
        etu = contexte_prof["etu_a"]

        r = client.post("/prof/notes", json={
            "matiere_id":  m1.id,
            "etudiant_id": etu.matricule,
            "valeur":      "14.50",
        }, headers=h)

        assert r.status_code == 201
        data = r.json()
        assert float(data["valeur"]) == 14.50
        assert data["matiere"]["nom"] == "Maths"

    def test_note_hors_plage(self, client, contexte_prof):
        """Valeur > 20 rejetée par Pydantic → 422."""
        h   = contexte_prof["headers"]
        m1  = contexte_prof["m1"]
        etu = contexte_prof["etu_a"]

        r = client.post("/prof/notes", json={
            "matiere_id":  m1.id,
            "etudiant_id": etu.matricule,
            "valeur":      "21",
        }, headers=h)
        assert r.status_code == 422

    def test_note_negative(self, client, contexte_prof):
        h   = contexte_prof["headers"]
        m1  = contexte_prof["m1"]
        etu = contexte_prof["etu_a"]

        r = client.post("/prof/notes", json={
            "matiere_id": m1.id, "etudiant_id": etu.matricule, "valeur": "-1",
        }, headers=h)
        assert r.status_code == 422

    def test_doublon_etudiant_matiere(self, client, contexte_prof):
        """Deux notes pour le même étudiant dans la même matière → 400."""
        h   = contexte_prof["headers"]
        m1  = contexte_prof["m1"]
        etu = contexte_prof["etu_a"]
        payload = {"matiere_id": m1.id, "etudiant_id": etu.matricule, "valeur": "12"}

        client.post("/prof/notes", json=payload, headers=h)
        r = client.post("/prof/notes", json=payload, headers=h)
        assert r.status_code == 400
        assert "existe déjà" in r.json()["detail"]

    def test_matiere_non_affectee(self, client, contexte_prof):
        """Saisir une note sur une matière non affectée → 403."""
        h   = contexte_prof["headers"]
        m2  = contexte_prof["m2"]   # prof1 n'est pas affecté à m2
        etu = contexte_prof["etu_a"]

        r = client.post("/prof/notes", json={
            "matiere_id": m2.id, "etudiant_id": etu.matricule, "valeur": "10",
        }, headers=h)
        assert r.status_code == 403


# ─────────────────────────────────────────────
# MODIFICATION DE NOTES
# ─────────────────────────────────────────────

class TestProfModificationNote:

    def _saisir_note(self, client, headers, m_id, etu_matricule, valeur="12"):
        r = client.post("/prof/notes", json={
            "matiere_id": m_id, "etudiant_id": etu_matricule, "valeur": valeur,
        }, headers=headers)
        assert r.status_code == 201
        return r.json()

    def test_modifier_sa_note(self, client, contexte_prof):
        h   = contexte_prof["headers"]
        m1  = contexte_prof["m1"]
        etu = contexte_prof["etu_a"]

        note = self._saisir_note(client, h, m1.id, etu.matricule)
        r = client.put(f"/prof/notes/{note['id']}", json={"valeur": "18"}, headers=h)

        assert r.status_code == 200
        assert float(r.json()["valeur"]) == 18.0

    def test_modifier_note_inexistante(self, client, contexte_prof):
        r = client.put("/prof/notes/9999", json={"valeur": "10"}, headers=contexte_prof["headers"])
        assert r.status_code == 404

    def test_modifier_note_autre_prof(self, client, contexte_prof, db):
        """Prof2 ne peut pas modifier une note saisie par Prof1."""
        h1  = contexte_prof["headers"]
        m1  = contexte_prof["m1"]
        etu = contexte_prof["etu_a"]

        note = self._saisir_note(client, h1, m1.id, etu.matricule)
        h2   = {"Authorization": f"Bearer {contexte_prof['token_prof2']}"}

        r = client.put(f"/prof/notes/{note['id']}", json={"valeur": "5"}, headers=h2)
        assert r.status_code == 403


# ─────────────────────────────────────────────
# SUPPRESSION DE NOTES
# ─────────────────────────────────────────────

class TestProfSuppressionNote:

    def _saisir_note(self, client, headers, m_id, etu_matricule):
        r = client.post("/prof/notes", json={
            "matiere_id": m_id, "etudiant_id": etu_matricule, "valeur": "12",
        }, headers=headers)
        assert r.status_code == 201
        return r.json()

    def test_supprimer_sa_note(self, client, contexte_prof):
        h   = contexte_prof["headers"]
        note = self._saisir_note(client, h, contexte_prof["m1"].id, contexte_prof["etu_a"].matricule)

        r = client.delete(f"/prof/notes/{note['id']}", headers=h)
        assert r.status_code == 204

        # La liste est vide
        assert client.get("/prof/notes", headers=h).json() == []

    def test_supprimer_note_inexistante(self, client, contexte_prof):
        r = client.delete("/prof/notes/9999", headers=contexte_prof["headers"])
        assert r.status_code == 404

    def test_supprimer_note_autre_prof(self, client, contexte_prof):
        h1   = contexte_prof["headers"]
        note = self._saisir_note(client, h1, contexte_prof["m1"].id, contexte_prof["etu_a"].matricule)
        h2   = {"Authorization": f"Bearer {contexte_prof['token_prof2']}"}

        r = client.delete(f"/prof/notes/{note['id']}", headers=h2)
        assert r.status_code == 403


# ─────────────────────────────────────────────
# MOYENNES PAR CLASSE
# ─────────────────────────────────────────────

class TestProfMoyennes:

    def _saisir_notes_contexte(self, client, ctx):
        """Saisit 2 notes pour avoir un classement."""
        h = ctx["headers"]
        client.post("/prof/notes", json={
            "matiere_id": ctx["m1"].id, "etudiant_id": ctx["etu_a"].matricule, "valeur": "16",
        }, headers=h)
        client.post("/prof/notes", json={
            "matiere_id": ctx["m1"].id, "etudiant_id": ctx["etu_b"].matricule, "valeur": "6",
        }, headers=h)

    def test_moyennes_sa_classe(self, client, contexte_prof):
        self._saisir_notes_contexte(client, contexte_prof)
        classe_id = contexte_prof["classe"].id
        h = contexte_prof["headers"]

        r = client.get(f"/prof/classes/{classe_id}/moyennes", headers=h)
        assert r.status_code == 200

        data = r.json()
        assert len(data) == 2
        # Ordre décroissant : etu_a (16) avant etu_b (6)
        assert data[0]["matricule"] == contexte_prof["etu_a"].matricule
        assert data[0]["rang"] == 1

    def test_moyennes_classe_non_affectee(self, client, contexte_prof, db):
        autre = Classe(libelle="Autre", annee_scolaire="2024-2025")
        db.add(autre)
        db.commit()
        db.refresh(autre)

        r = client.get(f"/prof/classes/{autre.id}/moyennes", headers=contexte_prof["headers"])
        assert r.status_code == 403

    def test_moyennes_classe_sans_notes(self, client, contexte_prof):
        """Classe affectée mais sans notes → liste vide."""
        r = client.get(
            f"/prof/classes/{contexte_prof['classe'].id}/moyennes",
            headers=contexte_prof["headers"],
        )
        assert r.status_code == 200
        assert r.json() == []