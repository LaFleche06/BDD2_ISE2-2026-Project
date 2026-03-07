"""
Tests — Admin : Statistiques & Classements

Routes testées :
    GET  /admin/stats
    GET  /admin/classement/{classe_id}
    POST /admin/classement/{classe_id}/sauvegarder
    GET  /admin/notes
    GET  /admin/notes?classe_id=...

Jeu de données (_creer_contexte_complet) :
    Matière Maths    coefficient=2
    Matière Histoire coefficient=1

    Étudiant A : Maths=16, Histoire=12
        moyenne = (16×2 + 12×1) / (2+1) = 44/3 ≈ 14.67  → Admis

    Étudiant B : Maths=6, Histoire=8
        moyenne = (6×2 + 8×1) / (2+1) = 20/3 ≈ 6.67   → Ajourné

    Moyenne établissement = (16×2 + 12×1 + 6×2 + 8×1) / (3+3) = 64/6 ≈ 10.67
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
# HELPER — jeu de données cohérent
# ─────────────────────────────────────────────

def _creer_contexte_complet(db):
    """
    Insère : 1 classe, 2 matières, 1 prof, 2 étudiants, 4 notes.
    Retourne (classe, etudiant_a, etudiant_b, matiere1, matiere2).
    """
    classe = Classe(libelle="Term A", annee_scolaire="2024-2025")
    db.add(classe)
    db.flush()

    m1 = Matiere(nom="Maths",   coefficient=Decimal("2.00"))
    m2 = Matiere(nom="Histoire", coefficient=Decimal("1.00"))
    db.add_all([m1, m2])
    db.flush()

    u_prof = Utilisateur(email="prof@test.com", mot_de_passe=hash_password("p"), role="prof", actif=True)
    db.add(u_prof)
    db.flush()
    prof = Professeur(utilisateur_id=u_prof.id, nom="Martin", prenom="Paul")
    db.add(prof)
    db.flush()

    # Étudiant A — bon élève
    u_a = Utilisateur(email="etua@test.com", mot_de_passe=hash_password("p"), role="etudiant", actif=True)
    db.add(u_a)
    db.flush()
    etu_a = Etudiant(utilisateur_id=u_a.id, classe_id=classe.id, nom="Dupont", prenom="Alice")
    db.add(etu_a)
    db.flush()

    # Étudiant B — en difficulté
    u_b = Utilisateur(email="etub@test.com", mot_de_passe=hash_password("p"), role="etudiant", actif=True)
    db.add(u_b)
    db.flush()
    etu_b = Etudiant(utilisateur_id=u_b.id, classe_id=classe.id, nom="Martin", prenom="Bob")
    db.add(etu_b)
    db.flush()

    now = datetime.now(timezone.utc)
    db.add_all([
        Note(matiere_id=m1.id, professeur_id=prof.id, etudiant_id=etu_a.matricule, valeur=Decimal("16"), date_saisie=now),
        Note(matiere_id=m2.id, professeur_id=prof.id, etudiant_id=etu_a.matricule, valeur=Decimal("12"), date_saisie=now),
        Note(matiere_id=m1.id, professeur_id=prof.id, etudiant_id=etu_b.matricule, valeur=Decimal("6"),  date_saisie=now),
        Note(matiere_id=m2.id, professeur_id=prof.id, etudiant_id=etu_b.matricule, valeur=Decimal("8"),  date_saisie=now),
    ])
    db.commit()
    db.refresh(etu_a)
    db.refresh(etu_b)
    return classe, etu_a, etu_b, m1, m2


# ─────────────────────────────────────────────
# STATS GLOBALES
# ─────────────────────────────────────────────

class TestStatsGlobales:

    def test_sans_token(self, client):
        assert client.get("/admin/stats").status_code == 401

    def test_compteurs_base_vide(self, client, headers_admin):
        r = client.get("/admin/stats", headers=headers_admin)
        assert r.status_code == 200
        data = r.json()
        assert data["nb_etudiants"]          == 0
        assert data["nb_professeurs"]         == 0
        assert data["nb_classes"]             == 0
        assert data["nb_matieres"]            == 0
        assert data["nb_notes"]               == 0
        assert data["moyenne_etablissement"]  is None
        assert data["taux_reussite_pct"]      is None

    def test_compteurs_apres_insertion(self, client, headers_admin, db):
        _creer_contexte_complet(db)
        r = client.get("/admin/stats", headers=headers_admin)
        assert r.status_code == 200
        data = r.json()
        assert data["nb_etudiants"]   == 2
        assert data["nb_professeurs"] == 1
        assert data["nb_classes"]     == 1
        assert data["nb_matieres"]    == 2
        assert data["nb_notes"]       == 4

    def test_moyenne_etablissement(self, client, headers_admin, db):
        """
        (16×2 + 12×1 + 6×2 + 8×1) / (2+1+2+1) = 64/6 ≈ 10.67
        Tolérance : ±0.05 pour les arrondis SQL.
        """
        _creer_contexte_complet(db)
        r = client.get("/admin/stats", headers=headers_admin)
        moyenne = r.json()["moyenne_etablissement"]
        assert moyenne is not None
        assert abs(moyenne - 10.67) < 0.05

    def test_taux_reussite(self, client, headers_admin, db):
        """1 admis (A) sur 2 → 50.0%."""
        _creer_contexte_complet(db)
        r = client.get("/admin/stats", headers=headers_admin)
        assert r.json()["taux_reussite_pct"] == 50.0


# ─────────────────────────────────────────────
# CLASSEMENT PAR CLASSE
# ─────────────────────────────────────────────

class TestClassement:

    def test_classe_inexistante(self, client, headers_admin):
        assert client.get("/admin/classement/9999", headers=headers_admin).status_code == 404

    def test_classe_sans_notes(self, client, headers_admin, db):
        classe = Classe(libelle="Vide", annee_scolaire="2024-2025")
        db.add(classe)
        db.commit()
        db.refresh(classe)

        r = client.get(f"/admin/classement/{classe.id}", headers=headers_admin)
        assert r.status_code == 200
        assert r.json()["classement"] == []

    def test_classement_ordre_et_rang(self, client, headers_admin, db):
        """Rang 1 = meilleure moyenne (étudiant A)."""
        classe, etu_a, etu_b, _, _ = _creer_contexte_complet(db)

        r = client.get(f"/admin/classement/{classe.id}", headers=headers_admin)
        assert r.status_code == 200

        classement = r.json()["classement"]
        assert len(classement) == 2
        assert classement[0]["rang"]       == 1
        assert classement[0]["matricule"]  == etu_a.matricule
        assert classement[1]["rang"]       == 2
        assert classement[1]["matricule"]  == etu_b.matricule

    def test_moyenne_ponderee(self, client, headers_admin, db):
        """
        A : (16×2 + 12×1) / 3 = 14.67
        B : (6×2  + 8×1)  / 3 =  6.67
        """
        classe, etu_a, etu_b, _, _ = _creer_contexte_complet(db)

        classement = client.get(
            f"/admin/classement/{classe.id}", headers=headers_admin
        ).json()["classement"]

        assert abs(classement[0]["moyenne"] - 14.67) < 0.05
        assert abs(classement[1]["moyenne"] -  6.67) < 0.05

    def test_decision_admis_ajourne(self, client, headers_admin, db):
        classe, _, _, _, _ = _creer_contexte_complet(db)
        classement = client.get(
            f"/admin/classement/{classe.id}", headers=headers_admin
        ).json()["classement"]

        assert classement[0]["decision"] == "Admis"    # 14.67 >= 10
        assert classement[1]["decision"] == "Ajourné"  # 6.67  < 10


# ─────────────────────────────────────────────
# SAUVEGARDE DES RÉSULTATS
# ─────────────────────────────────────────────

class TestSauvegardeClassement:

    def test_classe_sans_notes_retourne_400(self, client, headers_admin, db):
        classe = Classe(libelle="Vide", annee_scolaire="2024-2025")
        db.add(classe)
        db.commit()
        db.refresh(classe)

        r = client.post(f"/admin/classement/{classe.id}/sauvegarder", headers=headers_admin)
        assert r.status_code == 400
        assert "aucune note" in r.json()["detail"].lower()

    def test_sauvegarde_reussie(self, client, headers_admin, db):
        classe, etu_a, etu_b, _, _ = _creer_contexte_complet(db)

        r = client.post(f"/admin/classement/{classe.id}/sauvegarder", headers=headers_admin)
        assert r.status_code == 201
        assert "2" in r.json()["message"]

        resultats = db.query(Resultat).filter(Resultat.classe_id == classe.id).all()
        assert len(resultats) == 2

        res_a = next(r for r in resultats if r.etudiant_id == etu_a.matricule)
        assert res_a.decision == "Admis"
        assert res_a.rang == 1
        assert abs(float(res_a.moyenne_generale) - 14.67) < 0.05

    def test_resauvegarde_ecrase_anciens_resultats(self, client, headers_admin, db):
        """Deux sauvegardes consécutives → toujours exactement 2 résultats."""
        classe, _, _, _, _ = _creer_contexte_complet(db)

        client.post(f"/admin/classement/{classe.id}/sauvegarder", headers=headers_admin)
        client.post(f"/admin/classement/{classe.id}/sauvegarder", headers=headers_admin)

        count = db.query(Resultat).filter(Resultat.classe_id == classe.id).count()
        assert count == 2

    def test_classe_inexistante(self, client, headers_admin):
        r = client.post("/admin/classement/9999/sauvegarder", headers=headers_admin)
        assert r.status_code == 404


# ─────────────────────────────────────────────
# VUE GLOBALE DES NOTES
# ─────────────────────────────────────────────

class TestAdminNotes:

    def test_liste_vide(self, client, headers_admin):
        r = client.get("/admin/notes", headers=headers_admin)
        assert r.status_code == 200
        assert r.json() == []

    def test_toutes_les_notes(self, client, headers_admin, db):
        _creer_contexte_complet(db)
        r = client.get("/admin/notes", headers=headers_admin)
        assert r.status_code == 200
        assert len(r.json()) == 4   # 2 étudiants × 2 matières

    def test_filtre_par_classe(self, client, headers_admin, db):
        classe, _, _, _, _ = _creer_contexte_complet(db)

        r = client.get(f"/admin/notes?classe_id={classe.id}", headers=headers_admin)
        assert r.status_code == 200
        assert len(r.json()) == 4

    def test_filtre_classe_sans_notes(self, client, headers_admin, db):
        _creer_contexte_complet(db)
        autre = Classe(libelle="Autre", annee_scolaire="2024-2025")
        db.add(autre)
        db.commit()
        db.refresh(autre)

        r = client.get(f"/admin/notes?classe_id={autre.id}", headers=headers_admin)
        assert r.status_code == 200
        assert r.json() == []

    def test_sans_token(self, client):
        assert client.get("/admin/notes").status_code == 401