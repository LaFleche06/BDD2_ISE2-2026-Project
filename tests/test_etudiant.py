"""
Tests — Espace Étudiant

Routes testées :
    GET /etudiant/profil
    GET /etudiant/notes
    GET /etudiant/dashboard

Cas couverts :

    Sécurité :
        ✅ Sans token → 401
        ✅ Rôle prof → 403
        ✅ Un étudiant ne peut voir que ses propres données

    Profil :
        ✅ Retourne ses infos + sa classe

    Notes :
        ✅ Liste vide si aucune note
        ✅ Liste ses notes avec détail matière

    Dashboard :
        ✅ Moyenne pondérée calculée correctement
        ✅ Rang et décision None si aucun résultat officiel
        ✅ Rang et décision depuis le dernier résultat officiel
        ✅ Notes détaillées présentes
        ✅ Dashboard vide (aucune note) → moyenne None
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from models.models import (
    Utilisateur, Classe, Matiere, Etudiant,
    Professeur, Note, Resultat,
)
from core.security import hash_password


# ─────────────────────────────────────────────
# FIXTURE — contexte étudiant
# ─────────────────────────────────────────────

@pytest.fixture()
def contexte_etudiant(db, client):
    """
    Crée :
        - 1 classe
        - 2 matières (Maths coeff=2, Histoire coeff=1)
        - 1 prof
        - 1 étudiant principal (connecté dans les tests)
        - token JWT de l'étudiant

    Notes : aucune par défaut (ajoutées dans chaque test qui en a besoin).
    """
    classe = Classe(libelle="Term A", annee_scolaire="2024-2025")
    db.add(classe)
    db.flush()

    m1 = Matiere(nom="Maths",    coefficient=Decimal("2.00"))
    m2 = Matiere(nom="Histoire", coefficient=Decimal("1.00"))
    db.add_all([m1, m2])
    db.flush()

    u_prof = Utilisateur(email="prof@test.com", mot_de_passe=hash_password("p"), role="prof", actif=True)
    db.add(u_prof)
    db.flush()
    prof = Professeur(utilisateur_id=u_prof.id, nom="Dupont", prenom="Jean")
    db.add(prof)
    db.flush()

    u_etu = Utilisateur(email="etu@test.com", mot_de_passe=hash_password("pass1234"), role="etudiant", actif=True)
    db.add(u_etu)
    db.flush()
    etudiant = Etudiant(utilisateur_id=u_etu.id, classe_id=classe.id, nom="Diallo", prenom="Amara")
    db.add(etudiant)
    db.commit()
    db.refresh(etudiant)

    token = client.post("/auth/login", json={
        "email": "etu@test.com", "mot_de_passe": "pass1234",
    }).json()["access_token"]

    return {
        "etudiant": etudiant, "classe": classe,
        "m1": m1, "m2": m2, "prof": prof,
        "headers": {"Authorization": f"Bearer {token}"},
    }


def _ajouter_notes(db, ctx, valeur_m1="14", valeur_m2="10"):
    """Helper : insère des notes directement en base pour l'étudiant principal."""
    now = datetime.now(timezone.utc)
    db.add(Note(
        matiere_id=ctx["m1"].id, professeur_id=ctx["prof"].id,
        etudiant_id=ctx["etudiant"].matricule,
        valeur=Decimal(valeur_m1), date_saisie=now,
    ))
    db.add(Note(
        matiere_id=ctx["m2"].id, professeur_id=ctx["prof"].id,
        etudiant_id=ctx["etudiant"].matricule,
        valeur=Decimal(valeur_m2), date_saisie=now,
    ))
    db.commit()


# ─────────────────────────────────────────────
# SÉCURITÉ
# ─────────────────────────────────────────────

class TestEtudiantSecurite:

    def test_sans_token(self, client):
        assert client.get("/etudiant/profil").status_code     == 401
        assert client.get("/etudiant/notes").status_code      == 401
        assert client.get("/etudiant/dashboard").status_code  == 401

    def test_role_prof_refuse(self, client, db):
        """Un prof ne peut pas accéder aux routes étudiant."""
        u = Utilisateur(email="prof@test.com", mot_de_passe=hash_password("p"), role="prof", actif=True)
        db.add(u)
        db.flush()
        db.add(Professeur(utilisateur_id=u.id, nom="X", prenom="X"))
        db.commit()

        token = client.post("/auth/login", json={"email": "prof@test.com", "mot_de_passe": "p"}).json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        assert client.get("/etudiant/profil",    headers=h).status_code == 403
        assert client.get("/etudiant/notes",     headers=h).status_code == 403
        assert client.get("/etudiant/dashboard", headers=h).status_code == 403


# ─────────────────────────────────────────────
# PROFIL
# ─────────────────────────────────────────────

class TestEtudiantProfil:

    def test_profil_retourne_ses_infos(self, client, contexte_etudiant):
        h = contexte_etudiant["headers"]
        r = client.get("/etudiant/profil", headers=h)

        assert r.status_code == 200
        data = r.json()
        assert data["nom"]    == "Diallo"
        assert data["prenom"] == "Amara"
        assert data["matricule"] == contexte_etudiant["etudiant"].matricule

    def test_profil_inclut_classe(self, client, contexte_etudiant):
        r = client.get("/etudiant/profil", headers=contexte_etudiant["headers"])
        assert r.json()["classe"]["libelle"] == "Term A"


# ─────────────────────────────────────────────
# NOTES
# ─────────────────────────────────────────────

class TestEtudiantNotes:

    def test_notes_vides(self, client, contexte_etudiant):
        r = client.get("/etudiant/notes", headers=contexte_etudiant["headers"])
        assert r.status_code == 200
        assert r.json() == []

    def test_ses_notes_avec_detail(self, client, contexte_etudiant, db):
        _ajouter_notes(db, contexte_etudiant)
        r = client.get("/etudiant/notes", headers=contexte_etudiant["headers"])

        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2

        # Chaque note doit contenir le détail de la matière
        for note in data:
            assert "matiere" in note
            assert "nom" in note["matiere"]

    def test_ne_voit_pas_notes_des_autres(self, client, contexte_etudiant, db):
        """Un étudiant ne doit voir que ses propres notes."""
        # Créer un second étudiant avec des notes
        u2 = Utilisateur(email="etu2@test.com", mot_de_passe=hash_password("p"), role="etudiant", actif=True)
        db.add(u2)
        db.flush()
        etu2 = Etudiant(utilisateur_id=u2.id, classe_id=contexte_etudiant["classe"].id, nom="Autre", prenom="Autre")
        db.add(etu2)
        db.flush()
        db.add(Note(
            matiere_id=contexte_etudiant["m1"].id,
            professeur_id=contexte_etudiant["prof"].id,
            etudiant_id=etu2.matricule,
            valeur=Decimal("15"),
            date_saisie=datetime.now(timezone.utc),
        ))
        db.commit()

        # L'étudiant principal n'a pas de notes → sa liste doit être vide
        r = client.get("/etudiant/notes", headers=contexte_etudiant["headers"])
        assert r.json() == []


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────

class TestEtudiantDashboard:

    def test_dashboard_sans_notes(self, client, contexte_etudiant):
        """Sans notes, moyenne None, rang None, décision None, liste vide."""
        r = client.get("/etudiant/dashboard", headers=contexte_etudiant["headers"])
        assert r.status_code == 200

        data = r.json()
        assert data["moyenne_generale"] is None
        assert data["rang"]             is None
        assert data["decision"]         is None
        assert data["notes"]            == []

    def test_dashboard_infos_personnelles(self, client, contexte_etudiant):
        r = client.get("/etudiant/dashboard", headers=contexte_etudiant["headers"])
        data = r.json()
        assert data["nom"]           == "Diallo"
        assert data["classe"]        == "Term A"
        assert data["annee_scolaire"] == "2024-2025"

    def test_dashboard_moyenne_ponderee(self, client, contexte_etudiant, db):
        """
        Maths (coeff=2) : 14  +  Histoire (coeff=1) : 10
        Moyenne = (14×2 + 10×1) / 3 = 38/3 ≈ 12.67
        """
        _ajouter_notes(db, contexte_etudiant, valeur_m1="14", valeur_m2="10")

        r = client.get("/etudiant/dashboard", headers=contexte_etudiant["headers"])
        assert r.status_code == 200

        moyenne = float(r.json()["moyenne_generale"])
        assert abs(moyenne - 12.67) < 0.05

    def test_dashboard_notes_detaillees(self, client, contexte_etudiant, db):
        """Le dashboard inclut les notes avec matière et coefficient."""
        _ajouter_notes(db, contexte_etudiant)

        r = client.get("/etudiant/dashboard", headers=contexte_etudiant["headers"])
        notes = r.json()["notes"]

        assert len(notes) == 2
        for n in notes:
            assert "matiere"     in n
            assert "coefficient" in n
            assert "valeur"      in n

    def test_dashboard_rang_sans_resultat_officiel(self, client, contexte_etudiant, db):
        """Sans résultat officiel sauvegardé, rang et décision sont None."""
        _ajouter_notes(db, contexte_etudiant)

        r = client.get("/etudiant/dashboard", headers=contexte_etudiant["headers"])
        data = r.json()
        assert data["rang"]     is None
        assert data["decision"] is None

    def test_dashboard_rang_avec_resultat_officiel(self, client, contexte_etudiant, db):
        """Après sauvegarde admin, le dashboard reflète le rang officiel."""
        _ajouter_notes(db, contexte_etudiant)

        # Simule une sauvegarde admin directement en base
        db.add(Resultat(
            classe_id        = contexte_etudiant["classe"].id,
            etudiant_id      = contexte_etudiant["etudiant"].matricule,
            moyenne_generale = Decimal("12.67"),
            decision         = "Admis",
            annee_scolaire   = "2024-2025",
            rang             = 1,
        ))
        db.commit()

        r = client.get("/etudiant/dashboard", headers=contexte_etudiant["headers"])
        data = r.json()
        assert data["rang"]     == 1
        assert data["decision"] == "Admis"