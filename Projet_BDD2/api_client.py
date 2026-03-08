# ============================================================
# api_client.py - Couche d'accès à l'API REST (remplace db.py)
# ============================================================
import requests
from config import API_BASE_URL

# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------

def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _get(path: str, token: str, params: dict = None):
    """GET vers l'API, retourne le JSON ou None en cas d'erreur."""
    r = requests.get(f"{API_BASE_URL}{path}", headers=_headers(token), params=params, verify=False, timeout=15)
    if r.status_code == 200:
        return r.json()
    return None


def _post(path: str, token: str, payload: dict):
    r = requests.post(f"{API_BASE_URL}{path}", headers=_headers(token), json=payload, verify=False, timeout=15)
    return r


def _put(path: str, token: str, payload: dict = None):
    r = requests.put(f"{API_BASE_URL}{path}", headers=_headers(token), json=payload or {}, verify=False, timeout=15)
    return r


def _delete(path: str, token: str, payload: dict = None):
    r = requests.delete(f"{API_BASE_URL}{path}", headers=_headers(token), json=payload, verify=False, timeout=15)
    return r


# ---------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------

def login(email: str, mot_de_passe: str):
    """Retourne (token, role) ou (None, None) si échec."""
    r = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": email, "mot_de_passe": mot_de_passe},
        verify=False, timeout=15
    )
    if r.status_code == 200:
        data = r.json()
        return data["access_token"], data["role"]
    return None, None


def health_check():
    """Vérifie que l'API répond."""
    try:
        r = requests.get(f"{API_BASE_URL}/", verify=False, timeout=10)
        return r.status_code == 200, r.json()
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# PROFILS CONNECTÉS
# ---------------------------------------------------------------------------

def get_profil_etudiant(token: str):
    return _get("/etudiant/profil", token)


def get_profil_admin(token: str):
    return _get("/admin/profil", token)


def get_dashboard_etudiant(token: str):
    return _get("/etudiant/dashboard", token)


# ---------------------------------------------------------------------------
# ÉTUDIANTS (admin)
# ---------------------------------------------------------------------------

def get_all_etudiants(token: str):
    return _get("/admin/etudiants", token) or []


def get_etudiant(token: str, matricule: int):
    return _get(f"/admin/etudiants/{matricule}", token)


def get_etudiants_by_classe(token: str, classe_id: int):
    """Via l'endoint professeur (liste étudiants d'une classe)."""
    return _get(f"/prof/classes/{classe_id}/etudiants", token) or []


def create_etudiant(token: str, payload: dict):
    return _post("/admin/etudiants", token, payload)


def update_etudiant(token: str, matricule: int, payload: dict):
    return _put(f"/admin/etudiants/{matricule}", token, payload)


def delete_etudiant(token: str, matricule: int):
    return _delete(f"/admin/etudiants/{matricule}", token)


def get_notes_etudiant_admin(token: str, matricule: int):
    return _get(f"/admin/etudiants/{matricule}/notes", token) or []


# ---------------------------------------------------------------------------
# PROFESSEURS (admin)
# ---------------------------------------------------------------------------

def get_all_professeurs(token: str):
    return _get("/admin/professeurs", token) or []


def get_professeur(token: str, prof_id: int):
    return _get(f"/admin/professeurs/{prof_id}", token)


def create_professeur(token: str, payload: dict):
    return _post("/admin/professeurs", token, payload)


def update_professeur(token: str, prof_id: int, payload: dict):
    return _put(f"/admin/professeurs/{prof_id}", token, payload)


def delete_professeur(token: str, prof_id: int):
    return _delete(f"/admin/professeurs/{prof_id}", token)


# ---------------------------------------------------------------------------
# INTERVENTIONS (affectations prof → matière → classe)
# ---------------------------------------------------------------------------

def get_all_interventions(token: str):
    return _get("/admin/interventions", token) or []


def create_intervention(token: str, professeur_id: int, matiere_id: int, classe_id: int):
    return _post("/admin/interventions", token, {
        "professeur_id": professeur_id,
        "matiere_id": matiere_id,
        "classe_id": classe_id,
    })


def delete_intervention(token: str, professeur_id: int, matiere_id: int, classe_id: int):
    return _delete("/admin/interventions", token, {
        "professeur_id": professeur_id,
        "matiere_id": matiere_id,
        "classe_id": classe_id,
    })


def get_mes_interventions(token: str):
    """Pour le professeur connecté."""
    return _get("/prof/interventions", token) or []


# ---------------------------------------------------------------------------
# CLASSES
# ---------------------------------------------------------------------------

def get_all_classes(token: str):
    return _get("/admin/classes", token) or []


def create_classe(token: str, libelle: str, annee_scolaire: str = None):
    return _post("/admin/classes", token, {"libelle": libelle, "annee_scolaire": annee_scolaire or None})


def update_classe(token: str, classe_id: int, libelle: str = None, annee_scolaire: str = None):
    payload = {}
    if libelle is not None:
        payload["libelle"] = libelle
    if annee_scolaire is not None:
        payload["annee_scolaire"] = annee_scolaire
    return _put(f"/admin/classes/{classe_id}", token, payload)


def delete_classe(token: str, classe_id: int):
    return _delete(f"/admin/classes/{classe_id}", token)


# ---------------------------------------------------------------------------
# MATIÈRES
# ---------------------------------------------------------------------------

def get_all_matieres(token: str):
    return _get("/admin/matieres", token) or []


def create_matiere(token: str, nom: str, coefficient=None, volume_horaire: str = None):
    payload = {"nom": nom}
    if coefficient is not None:
        payload["coefficient"] = coefficient
    if volume_horaire:
        payload["volume_horaire"] = volume_horaire
    return _post("/admin/matieres", token, payload)


def update_matiere(token: str, matiere_id: int, nom: str = None, coefficient=None, volume_horaire: str = None):
    payload = {}
    if nom is not None:
        payload["nom"] = nom
    if coefficient is not None:
        payload["coefficient"] = coefficient
    if volume_horaire is not None:
        payload["volume_horaire"] = volume_horaire
    return _put(f"/admin/matieres/{matiere_id}", token, payload)


def delete_matiere(token: str, matiere_id: int):
    return _delete(f"/admin/matieres/{matiere_id}", token)


# ---------------------------------------------------------------------------
# NOTES — professeur
# ---------------------------------------------------------------------------

def get_mes_notes(token: str):
    return _get("/prof/notes", token) or []


def saisir_note(token: str, etudiant_id: int, matiere_id: int, valeur):
    return _post("/prof/notes", token, {
        "etudiant_id": etudiant_id,
        "matiere_id": matiere_id,
        "valeur": valeur,
    })


def modifier_note(token: str, note_id: int, valeur):
    return _put(f"/prof/notes/{note_id}", token, {"valeur": valeur})


def supprimer_note(token: str, note_id: int):
    return _delete(f"/prof/notes/{note_id}", token)


def get_mes_notes_etudiant(token: str):
    """Pour l'étudiant connecté."""
    return _get("/etudiant/notes", token) or []


# ---------------------------------------------------------------------------
# NOTES — admin
# ---------------------------------------------------------------------------

def get_all_notes_admin(token: str, classe_id: int = None):
    params = {"classe_id": classe_id} if classe_id else None
    return _get("/admin/notes", token, params=params) or []


# ---------------------------------------------------------------------------
# CLASSEMENTS & STATISTIQUES
# ---------------------------------------------------------------------------

def get_stats_globales(token: str):
    return _get("/admin/stats", token) or {}


def get_stats_classe(token: str, classe_id: int):
    return _get(f"/admin/stats/classes/{classe_id}", token) or {}


def get_classement_classe(token: str, classe_id: int):
    return _get(f"/admin/classement/{classe_id}", token) or []


def get_classement_prof(token: str, classe_id: int):
    """Classement provisoire pour le professeur."""
    return _get(f"/prof/classes/{classe_id}/moyennes", token) or []


def sauvegarder_classement(token: str, classe_id: int):
    return _post(f"/admin/classement/{classe_id}/sauvegarder", token, {})


def get_resultats_classe(token: str, classe_id: int):
    return _get(f"/admin/resultats/{classe_id}", token) or []


# ---------------------------------------------------------------------------
# GESTION DES COMPTES (admin)
# ---------------------------------------------------------------------------

def activer_compte(token: str, user_id: int):
    return _put(f"/admin/utilisateurs/{user_id}/activer", token)


def desactiver_compte(token: str, user_id: int):
    return _put(f"/admin/utilisateurs/{user_id}/desactiver", token)


def reset_password(token: str, user_id: int, nouveau_mot_de_passe: str):
    return _put(f"/admin/utilisateurs/{user_id}/reset-password", token,
                {"nouveau_mot_de_passe": nouveau_mot_de_passe})
