"""
Router Administrateur — Gestion des Utilisateurs & Interventions

Corrections  :
- Ajout GET  /admin/administrateurs/profil       → profil de l'admin connecté
- Ajout PUT  /admin/utilisateurs/{id}/activer    → activer un compte
- Ajout PUT  /admin/utilisateurs/{id}/desactiver → désactiver un compte
- Ajout GET  /admin/etudiants/{matricule}/notes  → notes d'un étudiant (vue admin)
- ProfesseurDetailResponse expose l'email (utilisateur imbriqué)
- EtudiantDetailResponse expose l'email (utilisateur imbriqué)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from database.session import get_db
from models.models import (
    Etudiant, Professeur, Utilisateur, Intervention,
    Administrateur, Note,
)
from schemas.schemas import (
    EtudiantCreate, EtudiantUpdate, EtudiantResponse, EtudiantDetailResponse,
    ProfesseurCreate, ProfesseurUpdate, ProfesseurResponse, ProfesseurDetailResponse,
    InterventionCreate, InterventionResponse,
    AdministrateurResponse, AdministrateurCreate, AdministrateurUpdate,
    UtilisateurUpdate, NoteResponse, NoteCreate, ResetPasswordRequest
)
from core.dependencies import require_role
from core.security import hash_password

router = APIRouter(prefix="/admin", tags=["Admin — Utilisateurs & Interventions"])
admin_only = Depends(require_role("admin"))


# ─────────────────────────────────────────────
# PROFIL ADMINISTRATEUR CONNECTÉ
# ─────────────────────────────────────────────

@router.get("/profil", response_model=AdministrateurResponse)
def mon_profil_admin(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin")),
):
    """Retourne les informations de l'administrateur connecté."""
    admin = db.query(Administrateur).options(
        joinedload(Administrateur.utilisateur)
    ).filter(
        Administrateur.utilisateur_id == current_user.id
    ).first()
    if admin is None:
        raise HTTPException(status_code=404, detail="Profil administrateur introuvable")
    return admin


@router.get("/administrateurs", response_model=list[AdministrateurResponse])
def list_administrateurs(db: Session = Depends(get_db), _=admin_only):
    """Retourne la liste de tous les administrateurs."""
    return db.query(Administrateur).options(joinedload(Administrateur.utilisateur)).all()


@router.post("/administrateurs", response_model=AdministrateurResponse, status_code=status.HTTP_201_CREATED)
def create_administrateur(data: AdministrateurCreate, db: Session = Depends(get_db), _=admin_only):
    """Crée un nouvel administrateur et son compte utilisateur."""
    if db.query(Utilisateur).filter(Utilisateur.email == data.email).first():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    try:
        utilisateur = Utilisateur(
            email=data.email,
            mot_de_passe=hash_password(data.mot_de_passe),
            role="admin",
            actif=True,
        )
        db.add(utilisateur)
        db.flush()

        admin = Administrateur(
            utilisateur_id=utilisateur.id,
            nom=data.nom,
            prenom=data.prenom,
            telephone=data.telephone,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Impossible de créer l'administrateur")

    return admin


# ─────────────────────────────────────────────
# ACTIVATION / DÉSACTIVATION DES COMPTES
# ─────────────────────────────────────────────

@router.put(
    "/utilisateurs/{user_id}/activer",
    summary="Activer un compte utilisateur",
)
def activer_compte(
    user_id: int,
    db: Session = Depends(get_db),
    _=admin_only,
):
    """Active un compte utilisateur désactivé."""
    user = db.query(Utilisateur).filter(Utilisateur.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.actif = True
    db.commit()
    return {"message": f"Compte {user.email} activé avec succès", "actif": True}


@router.put(
    "/utilisateurs/{user_id}/desactiver",
    summary="Désactiver un compte utilisateur",
)
def desactiver_compte(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin")),
):
    """
    Désactive un compte utilisateur (soft delete).
    Un admin ne peut pas désactiver son propre compte.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Vous ne pouvez pas désactiver votre propre compte"
        )
    user = db.query(Utilisateur).filter(Utilisateur.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.actif = False
    db.commit()
    return {"message": f"Compte {user.email} désactivé", "actif": False}


# ─────────────────────────────────────────────
# ÉTUDIANTS
# ─────────────────────────────────────────────

@router.get("/etudiants", response_model=list[EtudiantDetailResponse])
def list_etudiants(db: Session = Depends(get_db), _=admin_only):
    """Retourne la liste de tous les étudiants avec email et statut."""
    return db.query(Etudiant).options(
        joinedload(Etudiant.classe),
        joinedload(Etudiant.utilisateur)
    ).all()


@router.get("/etudiants/{matricule}", response_model=EtudiantDetailResponse)
def get_etudiant(matricule: int, db: Session = Depends(get_db), _=admin_only):
    """Retourne le détail d'un étudiant (avec email et statut du compte)."""
    etudiant = db.query(Etudiant).options(
        joinedload(Etudiant.classe),
        joinedload(Etudiant.utilisateur)
    ).filter(Etudiant.matricule == matricule).first()
    if etudiant is None:
        raise HTTPException(status_code=404, detail="Étudiant introuvable")
    return etudiant


@router.get("/etudiants/{matricule}/notes", response_model=list[NoteResponse])
def notes_etudiant(matricule: int, db: Session = Depends(get_db), _=admin_only):
    """Retourne toutes les notes d'un étudiant (vue administrative)."""
    etudiant = db.query(Etudiant).filter(Etudiant.matricule == matricule).first()
    if etudiant is None:
        raise HTTPException(status_code=404, detail="Étudiant introuvable")
    return db.query(Note).filter(Note.etudiant_id == matricule).all()


@router.post("/etudiants/{matricule}/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def admin_ajouter_note(
    matricule: int,
    data: NoteCreate,
    db: Session = Depends(get_db),
    _=admin_only,
):
    """Saisit une note pour un étudiant (par l'administrateur)."""
    from datetime import datetime, timezone
    
    etudiant = db.query(Etudiant).filter(Etudiant.matricule == matricule).first()
    if not etudiant:
        raise HTTPException(status_code=404, detail="Étudiant introuvable")

    # Chercher le professeur en charge de cette matière dans la classe
    intervention = db.query(Intervention).filter(
        Intervention.matiere_id == data.matiere_id,
        Intervention.classe_id == etudiant.classe_id
    ).first()
    if not intervention:
        raise HTTPException(status_code=400, detail="Aucun professeur n'enseigne cette matière dans cette classe.")

    # Vérifier si l'étudiant a déjà une note
    existing = db.query(Note).filter(
        Note.etudiant_id == matricule,
        Note.matiere_id == data.matiere_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="L'étudiant a déjà une note dans cette matière.")

    note = Note(
        matiere_id=data.matiere_id,
        professeur_id=intervention.professeur_id,
        etudiant_id=matricule,
        valeur=data.valeur,
        date_saisie=data.date_saisie or datetime.now(timezone.utc),
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.post("/etudiants", response_model=EtudiantResponse, status_code=status.HTTP_201_CREATED)
def create_etudiant(data: EtudiantCreate, db: Session = Depends(get_db), _=admin_only):
    """Crée un étudiant et son compte utilisateur associé."""
    if db.query(Utilisateur).filter(Utilisateur.email == data.email).first():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    try:
        utilisateur = Utilisateur(
            email=data.email,
            mot_de_passe=hash_password(data.mot_de_passe),
            role="etudiant",
            actif=True,
        )
        db.add(utilisateur)
        db.flush()

        etudiant = Etudiant(
            utilisateur_id=utilisateur.id,
            classe_id=data.classe_id,
            nom=data.nom,
            prenom=data.prenom,
            telephone=data.telephone,
        )
        db.add(etudiant)
        db.commit()
        db.refresh(etudiant)

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Impossible de créer l'étudiant")

    return etudiant


@router.put("/etudiants/{matricule}", response_model=EtudiantResponse)
def update_etudiant(
    matricule: int, data: EtudiantUpdate,
    db: Session = Depends(get_db), _=admin_only,
):
    """Modifie les informations d'un étudiant (mise à jour partielle)."""
    etudiant = db.query(Etudiant).filter(Etudiant.matricule == matricule).first()
    if etudiant is None:
        raise HTTPException(status_code=404, detail="Étudiant introuvable")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(etudiant, field, value)

    try:
        db.commit()
        db.refresh(etudiant)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erreur lors de la modification")

    return etudiant


@router.delete("/etudiants/{matricule}", status_code=status.HTTP_204_NO_CONTENT)
def delete_etudiant(matricule: int, db: Session = Depends(get_db), _=admin_only):
    """Supprime un étudiant et son compte utilisateur en cascade."""
    etudiant = db.query(Etudiant).filter(Etudiant.matricule == matricule).first()
    if etudiant is None:
        raise HTTPException(status_code=404, detail="Étudiant introuvable")

    try:
        utilisateur_id = etudiant.utilisateur_id
        db.delete(etudiant)
        db.flush()
        utilisateur = db.query(Utilisateur).filter(Utilisateur.id == utilisateur_id).first()
        if utilisateur:
            db.delete(utilisateur)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Impossible de supprimer cet étudiant")


# ─────────────────────────────────────────────
# PROFESSEURS
# ─────────────────────────────────────────────

@router.get("/professeurs", response_model=list[ProfesseurDetailResponse])
def list_professeurs(db: Session = Depends(get_db), _=admin_only):
    """Retourne tous les professeurs avec email et statut du compte."""
    return db.query(Professeur).all()


@router.get("/professeurs/{prof_id}", response_model=ProfesseurDetailResponse)
def get_professeur(prof_id: int, db: Session = Depends(get_db), _=admin_only):
    """Retourne le détail d'un professeur."""
    prof = db.query(Professeur).filter(Professeur.id == prof_id).first()
    if prof is None:
        raise HTTPException(status_code=404, detail="Professeur introuvable")
    return prof


@router.post("/professeurs", response_model=ProfesseurResponse, status_code=status.HTTP_201_CREATED)
def create_professeur(data: ProfesseurCreate, db: Session = Depends(get_db), _=admin_only):
    """Crée un professeur et son compte utilisateur."""
    if db.query(Utilisateur).filter(Utilisateur.email == data.email).first():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    try:
        utilisateur = Utilisateur(
            email=data.email,
            mot_de_passe=hash_password(data.mot_de_passe),
            role="prof",
            actif=True,
        )
        db.add(utilisateur)
        db.flush()

        prof = Professeur(
            utilisateur_id=utilisateur.id,
            nom=data.nom,
            prenom=data.prenom,
            telephone=data.telephone,
        )
        db.add(prof)
        db.commit()
        db.refresh(prof)

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Impossible de créer le professeur")

    return prof


@router.put("/professeurs/{prof_id}", response_model=ProfesseurResponse)
def update_professeur(
    prof_id: int, data: ProfesseurUpdate,
    db: Session = Depends(get_db), _=admin_only,
):
    """Modifie un professeur (mise à jour partielle)."""
    prof = db.query(Professeur).filter(Professeur.id == prof_id).first()
    if prof is None:
        raise HTTPException(status_code=404, detail="Professeur introuvable")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(prof, field, value)

    try:
        db.commit()
        db.refresh(prof)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erreur lors de la modification")

    return prof


@router.delete("/professeurs/{prof_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_professeur(prof_id: int, db: Session = Depends(get_db), _=admin_only):
    """Supprime un professeur et son compte utilisateur en cascade."""
    prof = db.query(Professeur).filter(Professeur.id == prof_id).first()
    if prof is None:
        raise HTTPException(status_code=404, detail="Professeur introuvable")

    try:
        utilisateur_id = prof.utilisateur_id
        # Supprimer d'abord les notes liées au professeur
        db.query(Note).filter(Note.professeur_id == prof_id).delete(synchronize_session=False)
        # Supprimer les interventions (clé composite incluant professeur_id)
        db.query(Intervention).filter(Intervention.professeur_id == prof_id).delete(synchronize_session=False)
        db.flush()
        db.delete(prof)
        db.flush()
        utilisateur = db.query(Utilisateur).filter(Utilisateur.id == utilisateur_id).first()
        if utilisateur:
            db.delete(utilisateur)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Impossible de supprimer ce professeur")


# ─────────────────────────────────────────────
# INTERVENTIONS
# ─────────────────────────────────────────────

@router.get("/interventions", response_model=list[InterventionResponse])
def list_interventions(db: Session = Depends(get_db), _=admin_only):
    """Retourne toutes les affectations prof → matière → classe."""
    return db.query(Intervention).all()


@router.post("/interventions", response_model=InterventionResponse, status_code=status.HTTP_201_CREATED)
def create_intervention(data: InterventionCreate, db: Session = Depends(get_db), _=admin_only):
    """Crée une affectation professeur → matière → classe."""
    existing = db.query(Intervention).filter(
        Intervention.matiere_id    == data.matiere_id,
        Intervention.classe_id     == data.classe_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Une affectation existe déjà pour cette matière et cette classe")

    try:
        intervention = Intervention(**data.model_dump())
        db.add(intervention)
        db.commit()
        db.refresh(intervention)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Impossible de créer cette affectation")

    return intervention


@router.delete("/interventions", status_code=status.HTTP_204_NO_CONTENT)
def delete_intervention(data: InterventionCreate, db: Session = Depends(get_db), _=admin_only):
    """Supprime une affectation par la clé composite (prof + matière + classe)."""
    intervention = db.query(Intervention).filter(
        Intervention.professeur_id == data.professeur_id,
        Intervention.matiere_id    == data.matiere_id,
        Intervention.classe_id     == data.classe_id,
    ).first()
    if intervention is None:
        raise HTTPException(status_code=404, detail="Affectation introuvable")

    db.delete(intervention)
    db.commit()

@router.put("/utilisateurs/{user_id}/reset-password", summary="Réinitialiser le mot de passe")
def reset_password(
    user_id: int,
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
    _=admin_only,
):
    """L'admin réinitialise le mot de passe d'un utilisateur."""
    user = db.query(Utilisateur).filter(Utilisateur.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.mot_de_passe = hash_password(data.nouveau_mot_de_passe)
    db.commit()
    return {"message": f"Mot de passe réinitialisé pour {user.email}"}