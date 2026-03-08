"""
Tests — Admin : Activation/Désactivation comptes + Profil admin

Routes testées :
    GET /admin/profil
    PUT /admin/utilisateurs/{id}/activer
    PUT /admin/utilisateurs/{id}/desactiver
    GET /admin/etudiants/{matricule}/notes

Cas couverts :
    ✅ Admin voit son profil
    ✅ Activer un compte désactivé
    ✅ Désactiver un compte actif
    ✅ Un admin ne peut pas désactiver son propre compte → 400
    ✅ Utilisateur inexistant → 404
    ✅ Compte désactivé ne peut plus se connecter → 403
    ✅ Réactivation permet la reconnexion
    ✅ Notes d'un étudiant (vue admin)
"""

import pytest
from models.models import Utilisateur, Classe, Etudiant, Professeur, Note, Matiere, Administrateur
from core.security import hash_password
from decimal import Decimal
from datetime import datetime, timezone


def _post_classe(client, headers, libelle="Term A"):
    r = client.post("/admin/classes", json={"libelle": libelle, "annee_scolaire": "2024-2025"}, headers=headers)
    assert r.status_code == 201
    return r.json()


def _post_etudiant(client, headers, classe_id, email="etu@test.com"):
    r = client.post("/admin/etudiants", json={
        "nom": "Test", "prenom": "User",
        "email": email, "mot_de_passe": "pass1234",
        "classe_id": classe_id,
    }, headers=headers)
    assert r.status_code == 201
    return r.json()


class TestProfilAdmin:

    def test_profil_admin_sans_entite(self, client, headers_admin, admin_en_base):
        """
        L'admin créé par la fixture n'a pas d'entité Administrateur → 404.
        C'est normal : la fixture crée uniquement un Utilisateur.
        """
        r = client.get("/admin/profil", headers=headers_admin)
        # 404 attendu car admin_en_base ne crée pas l'entité Administrateur
        assert r.status_code == 404

    def test_profil_admin_avec_entite(self, client, db):
        """Un admin avec son entité Administrateur peut accéder à son profil."""
        u = Utilisateur(
            email="admin2@test.com",
            mot_de_passe=hash_password("Admin1234!"),
            role="admin", actif=True,
        )
        db.add(u)
        db.flush()
        db.add(Administrateur(utilisateur_id=u.id, nom="Admin", prenom="Super"))
        db.commit()

        token = client.post("/auth/login", json={
            "email": "admin2@test.com", "mot_de_passe": "Admin1234!",
        }).json()["access_token"]

        r = client.get("/admin/profil", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert data["nom"]    == "Admin"
        assert data["prenom"] == "Super"


class TestActivationCompte:

    def test_desactiver_compte_etudiant(self, client, headers_admin):
        """Désactiver un étudiant → son compte passe actif=False."""
        classe = _post_classe(client, headers_admin)
        etu = _post_etudiant(client, headers_admin, classe["id"])
        user_id = etu["utilisateur_id"]

        r = client.put(f"/admin/utilisateurs/{user_id}/desactiver", headers=headers_admin)
        assert r.status_code == 200
        assert r.json()["actif"] is False

    def test_compte_desactive_ne_peut_pas_se_connecter(self, client, headers_admin):
        """Après désactivation, le login doit retourner 403."""
        classe = _post_classe(client, headers_admin)
        _post_etudiant(client, headers_admin, classe["id"], "desactive@test.com")

        # Récupérer l'utilisateur_id
        r_list = client.get("/admin/etudiants", headers=headers_admin)
        user_id = r_list.json()[0]["utilisateur_id"]

        # Désactiver
        client.put(f"/admin/utilisateurs/{user_id}/desactiver", headers=headers_admin)

        # Tentative de connexion → 403
        r = client.post("/auth/login", json={
            "email": "desactive@test.com", "mot_de_passe": "pass1234",
        })
        assert r.status_code == 403

    def test_activer_compte_desactive(self, client, headers_admin):
        """Réactiver un compte → l'étudiant peut se reconnecter."""
        classe = _post_classe(client, headers_admin)
        _post_etudiant(client, headers_admin, classe["id"], "reactiver@test.com")

        r_list = client.get("/admin/etudiants", headers=headers_admin)
        user_id = r_list.json()[0]["utilisateur_id"]

        # Désactiver puis réactiver
        client.put(f"/admin/utilisateurs/{user_id}/desactiver", headers=headers_admin)
        r = client.put(f"/admin/utilisateurs/{user_id}/activer", headers=headers_admin)
        assert r.status_code == 200
        assert r.json()["actif"] is True

        # Connexion fonctionne de nouveau
        r_login = client.post("/auth/login", json={
            "email": "reactiver@test.com", "mot_de_passe": "pass1234",
        })
        assert r_login.status_code == 200

    def test_admin_ne_peut_pas_se_desactiver(self, client, headers_admin, admin_en_base):
        """Un admin ne peut pas désactiver son propre compte → 400."""
        r = client.put(
            f"/admin/utilisateurs/{admin_en_base.id}/desactiver",
            headers=headers_admin,
        )
        assert r.status_code == 400
        assert "propre compte" in r.json()["detail"].lower()

    def test_utilisateur_inexistant_activer(self, client, headers_admin):
        r = client.put("/admin/utilisateurs/9999/activer", headers=headers_admin)
        assert r.status_code == 404

    def test_utilisateur_inexistant_desactiver(self, client, headers_admin):
        r = client.put("/admin/utilisateurs/9999/desactiver", headers=headers_admin)
        assert r.status_code == 404


class TestNotesEtudiantAdmin:

    def test_notes_etudiant_vue_admin(self, client, headers_admin, db):
        """L'admin peut consulter les notes d'un étudiant spécifique."""
        classe = _post_classe(client, headers_admin)
        etu = _post_etudiant(client, headers_admin, classe["id"])

        # Insérer des notes directement en base
        m = Matiere(nom="Physique", coefficient=Decimal("1.00"))
        db.add(m)
        db.flush()
        u_p = Utilisateur(email="p@t.com", mot_de_passe=hash_password("p"), role="prof", actif=True)
        db.add(u_p)
        db.flush()
        prof = Professeur(utilisateur_id=u_p.id, nom="P", prenom="P")
        db.add(prof)
        db.flush()
        db.add(Note(
            matiere_id=m.id, professeur_id=prof.id,
            etudiant_id=etu["matricule"], valeur=Decimal("15"),
            date_saisie=datetime.now(timezone.utc),
        ))
        db.commit()

        r = client.get(f"/admin/etudiants/{etu['matricule']}/notes", headers=headers_admin)
        assert r.status_code == 200
        notes = r.json()
        assert len(notes) == 1
        assert float(notes[0]["valeur"]) == 15.0

    def test_notes_etudiant_inexistant(self, client, headers_admin):
        r = client.get("/admin/etudiants/9999/notes", headers=headers_admin)
        assert r.status_code == 404

    def test_notes_etudiant_vide(self, client, headers_admin):
        classe = _post_classe(client, headers_admin)
        etu = _post_etudiant(client, headers_admin, classe["id"])

        r = client.get(f"/admin/etudiants/{etu['matricule']}/notes", headers=headers_admin)
        assert r.status_code == 200
        assert r.json() == []