"""
Tests — Features v3
    PUT /admin/utilisateurs/{id}/reset-password
    GET /admin/stats/classes/{classe_id}
    GET /admin/resultats/{classe_id}
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from models.models import (
    Utilisateur, Classe, Matiere, Etudiant,
    Professeur, Note, Resultat,
)
from core.security import hash_password, verify_password


def _creer_contexte(db):
    classe = Classe(libelle="Term A", annee_scolaire="2024-2025")
    db.add(classe)
    db.flush()

    m1 = Matiere(nom="Maths",    coefficient=Decimal("2.00"))
    m2 = Matiere(nom="Histoire", coefficient=Decimal("1.00"))
    db.add_all([m1, m2])
    db.flush()

    u_prof = Utilisateur(email="prof@v3.com", mot_de_passe=hash_password("p"), role="prof", actif=True)
    db.add(u_prof)
    db.flush()
    prof = Professeur(utilisateur_id=u_prof.id, nom="P", prenom="P")
    db.add(prof)
    db.flush()

    u_a = Utilisateur(email="a@v3.com", mot_de_passe=hash_password("p"), role="etudiant", actif=True)
    db.add(u_a)
    db.flush()
    etu_a = Etudiant(utilisateur_id=u_a.id, classe_id=classe.id, nom="Alice", prenom="A")
    db.add(etu_a)
    db.flush()

    u_b = Utilisateur(email="b@v3.com", mot_de_passe=hash_password("p"), role="etudiant", actif=True)
    db.add(u_b)
    db.flush()
    etu_b = Etudiant(utilisateur_id=u_b.id, classe_id=classe.id, nom="Bob", prenom="B")
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
    return classe, etu_a, etu_b, u_a, u_b


# ─────────────────────────────────────────────
# RESET MOT DE PASSE
# ─────────────────────────────────────────────

class TestResetPassword:

    def test_reset_valide(self, client, headers_admin, db):
        classe, _, _, u_a, _ = _creer_contexte(db)
        r = client.put(
            f"/admin/utilisateurs/{u_a.id}/reset-password",
            json={"nouveau_mot_de_passe": "nouveau123"},
            headers=headers_admin,
        )
        assert r.status_code == 200
        # Vérifier que le nouveau hash fonctionne
        db.refresh(u_a)
        assert verify_password("nouveau123", u_a.mot_de_passe)

    def test_reset_ancien_mdp_invalide_apres(self, client, headers_admin, db):
        classe, _, _, u_a, _ = _creer_contexte(db)
        client.put(
            f"/admin/utilisateurs/{u_a.id}/reset-password",
            json={"nouveau_mot_de_passe": "nouveau123"},
            headers=headers_admin,
        )
        db.refresh(u_a)
        assert not verify_password("p", u_a.mot_de_passe)

    def test_reset_mdp_trop_court(self, client, headers_admin, db):
        classe, _, _, u_a, _ = _creer_contexte(db)
        r = client.put(
            f"/admin/utilisateurs/{u_a.id}/reset-password",
            json={"nouveau_mot_de_passe": "abc"},
            headers=headers_admin,
        )
        assert r.status_code == 422

    def test_reset_user_inexistant(self, client, headers_admin):
        r = client.put(
            "/admin/utilisateurs/9999/reset-password",
            json={"nouveau_mot_de_passe": "nouveau123"},
            headers=headers_admin,
        )
        assert r.status_code == 404

    def test_reset_sans_token(self, client):
        r = client.put(
            "/admin/utilisateurs/1/reset-password",
            json={"nouveau_mot_de_passe": "nouveau123"},
        )
        assert r.status_code == 401


# ─────────────────────────────────────────────
# STATS PAR CLASSE
# ─────────────────────────────────────────────

class TestStatsClasse:

    def test_classe_inexistante(self, client, headers_admin):
        assert client.get("/admin/stats/classes/9999", headers=headers_admin).status_code == 404

    def test_classe_sans_notes(self, client, headers_admin, db):
        classe = Classe(libelle="Vide", annee_scolaire="2024-2025")
        db.add(classe)
        db.commit()
        db.refresh(classe)

        r = client.get(f"/admin/stats/classes/{classe.id}", headers=headers_admin)
        assert r.status_code == 200
        data = r.json()
        assert data["nb_etudiants"]      == 0
        assert data["taux_reussite_pct"] is None
        assert data["moyenne_classe"]    is None

    def test_stats_correctes(self, client, headers_admin, db):
        """
        A : (16×2 + 12×1) / 3 = 14.67 → Admis
        B : (6×2  + 8×1)  / 3 =  6.67 → Ajourné
        moyenne_classe = (14.67 + 6.67) / 2 ≈ 10.67
        taux = 50%
        """
        classe, _, _, _, _ = _creer_contexte(db)
        r = client.get(f"/admin/stats/classes/{classe.id}", headers=headers_admin)
        assert r.status_code == 200
        data = r.json()

        assert data["nb_etudiants"]      == 2
        assert data["nb_admis"]          == 1
        assert data["nb_ajournes"]       == 1
        assert data["taux_reussite_pct"] == 50.0
        assert abs(data["moyenne_classe"]    - 10.67) < 0.05
        assert abs(data["meilleure_moyenne"] - 14.67) < 0.05
        assert abs(data["moins_bonne_moyenne"] - 6.67) < 0.05


# ─────────────────────────────────────────────
# RÉSULTATS SAUVEGARDÉS
# ─────────────────────────────────────────────

class TestResultatsClasse:

    def test_classe_inexistante(self, client, headers_admin):
        assert client.get("/admin/resultats/9999", headers=headers_admin).status_code == 404

    def test_vide_avant_sauvegarde(self, client, headers_admin, db):
        classe, _, _, _, _ = _creer_contexte(db)
        r = client.get(f"/admin/resultats/{classe.id}", headers=headers_admin)
        assert r.status_code == 200
        assert r.json() == []

    def test_resultats_apres_sauvegarde(self, client, headers_admin, db):
        classe, etu_a, etu_b, _, _ = _creer_contexte(db)

        client.post(f"/admin/classement/{classe.id}/sauvegarder", headers=headers_admin)

        r = client.get(f"/admin/resultats/{classe.id}", headers=headers_admin)
        assert r.status_code == 200
        resultats = r.json()

        assert len(resultats) == 2
        # Triés par rang
        assert resultats[0]["rang"] == 1
        assert resultats[1]["rang"] == 2

    def test_ordre_par_rang(self, client, headers_admin, db):
        classe, etu_a, _, _, _ = _creer_contexte(db)
        client.post(f"/admin/classement/{classe.id}/sauvegarder", headers=headers_admin)

        resultats = client.get(f"/admin/resultats/{classe.id}", headers=headers_admin).json()
        assert resultats[0]["etudiant_id"] == etu_a.matricule

    def test_sans_token(self, client, db):
        classe, _, _, _, _ = _creer_contexte(db)
        assert client.get(f"/admin/resultats/{classe.id}").status_code == 401