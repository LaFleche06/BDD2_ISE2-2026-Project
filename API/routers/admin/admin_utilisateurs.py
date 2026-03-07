"""
Router Administrateur — Gestion des Étudiants et Professeurs
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database.session import get_db
from models.models import Etudiant, Professeur, Utilisateur, Intervention
from schemas.schemas import (
    EtudiantCreate, EtudiantUpdate, EtudiantResponse,
    ProfesseurCreate, ProfesseurUpdate, ProfesseurResponse,
    InterventionCreate, InterventionResponse,
)
from core.dependencies import require_role
from core.security import hash_password

router = APIRouter(prefix="/admin", tags=["Admin — Utilisateurs & Interventions"])
admin_only = Depends(require_role("admin"))


# ─────────────────────────────────────────────
# ÉTUDIANTS
# ─────────────────────────────────────────────

@router.get("/etudiants", response_model=list[EtudiantResponse])
def list_etudiants(db: Session = Depends(get_db), _=admin_only):
    """Retourne la liste de tous les étudiants."""
    return db.query(Etudiant).all()


@router.get("/etudiants/{matricule}", response_model=EtudiantResponse)
def get_etudiant(matricule: int, db: Session = Depends(get_db), _=admin_only):
    """Retourne le détail d'un étudiant."""
    etudiant = db.query(Etudiant).filter(Etudiant.matricule == matricule).first()

    if etudiant is None:
        raise HTTPException(status_code=404, detail="Étudiant introuvable")

    return etudiant


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
        raise HTTPException(
            status_code=400,
            detail="Impossible de créer l'étudiant"
        )

    return etudiant


@router.put("/etudiants/{matricule}", response_model=EtudiantResponse)
def update_etudiant(matricule: int, data: EtudiantUpdate, db: Session = Depends(get_db), _=admin_only):
    """Modifie les informations d'un étudiant."""

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
        raise HTTPException(
            status_code=400,
            detail="Erreur lors de la modification"
        )

    return etudiant


@router.delete("/etudiants/{matricule}", status_code=status.HTTP_204_NO_CONTENT)
def delete_etudiant(matricule: int, db: Session = Depends(get_db), _=admin_only):
    """Supprime un étudiant et son compte utilisateur."""

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
        raise HTTPException(
            status_code=400,
            detail="Impossible de supprimer cet étudiant"
        )


# ─────────────────────────────────────────────
# PROFESSEURS
# ─────────────────────────────────────────────

@router.get("/professeurs", response_model=list[ProfesseurResponse])
def list_professeurs(db: Session = Depends(get_db), _=admin_only):
    """Retourne tous les professeurs."""
    return db.query(Professeur).all()


@router.get("/professeurs/{prof_id}", response_model=ProfesseurResponse)
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
        raise HTTPException(
            status_code=400,
            detail="Impossible de créer le professeur"
        )

    return prof


@router.put("/professeurs/{prof_id}", response_model=ProfesseurResponse)
def update_professeur(prof_id: int, data: ProfesseurUpdate, db: Session = Depends(get_db), _=admin_only):
    """Modifie un professeur."""

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
        raise HTTPException(
            status_code=400,
            detail="Erreur lors de la modification"
        )

    return prof


@router.delete("/professeurs/{prof_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_professeur(prof_id: int, db: Session = Depends(get_db), _=admin_only):
    """Supprime un professeur et son compte."""

    prof = db.query(Professeur).filter(Professeur.id == prof_id).first()

    if prof is None:
        raise HTTPException(status_code=404, detail="Professeur introuvable")

    try:
        utilisateur_id = prof.utilisateur_id

        db.delete(prof)
        db.flush()

        utilisateur = db.query(Utilisateur).filter(Utilisateur.id == utilisateur_id).first()

        if utilisateur:
            db.delete(utilisateur)

        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Impossible de supprimer ce professeur"
        )


# ─────────────────────────────────────────────
# INTERVENTIONS
# ─────────────────────────────────────────────

@router.get("/interventions", response_model=list[InterventionResponse])
def list_interventions(db: Session = Depends(get_db), _=admin_only):
    """Retourne toutes les affectations."""
    return db.query(Intervention).all()


@router.post("/interventions", response_model=InterventionResponse, status_code=status.HTTP_201_CREATED)
def create_intervention(data: InterventionCreate, db: Session = Depends(get_db), _=admin_only):
    """Crée une affectation professeur → matière → classe."""

    existing = db.query(Intervention).filter(
        Intervention.professeur_id == data.professeur_id,
        Intervention.matiere_id == data.matiere_id,
        Intervention.classe_id == data.classe_id,
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Cette affectation existe déjà")

    try:
        intervention = Intervention(**data.model_dump())

        db.add(intervention)
        db.commit()
        db.refresh(intervention)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Impossible de créer cette affectation"
        )

    return intervention


@router.delete("/interventions", status_code=status.HTTP_204_NO_CONTENT)
def delete_intervention(data: InterventionCreate, db: Session = Depends(get_db), _=admin_only):
    """Supprime une affectation."""

    intervention = db.query(Intervention).filter(
        Intervention.professeur_id == data.professeur_id,
        Intervention.matiere_id == data.matiere_id,
        Intervention.classe_id == data.classe_id,
    ).first()

    if intervention is None:
        raise HTTPException(status_code=404, detail="Affectation introuvable")

    db.delete(intervention)
    db.commit()