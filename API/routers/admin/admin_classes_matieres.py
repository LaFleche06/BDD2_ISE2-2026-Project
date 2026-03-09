"""
Router Administrateur — Gestion des Classes et Matières

Endpoints :
    Classes :
        GET    /admin/classes           => liste toutes les classes
        POST   /admin/classes           => créer une classe
        PUT    /admin/classes/{id}      => modifier une classe
        DELETE /admin/classes/{id}      => supprimer une classe

    Matières :
        GET    /admin/matieres          => liste toutes les matières
        POST   /admin/matieres          => créer une matière
        PUT    /admin/matieres/{id}     => modifier une matière
        DELETE /admin/matieres/{id}     => supprimer une matière
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database.session import get_db
from models.models import Classe, Matiere, Intervention
from schemas.schemas import (
    ClasseCreate, ClasseUpdate, ClasseResponse,
    MatiereCreate, MatiereUpdate, MatiereResponse,
    InterventionResponse,
)
from core.dependencies import require_role

router = APIRouter(prefix="/admin", tags=["Admin — Classes & Matières"])

admin_only = Depends(require_role("admin"))


# ─────────────────────────────────────────────
# CLASSES
# ─────────────────────────────────────────────

@router.get("/classes", response_model=list[ClasseResponse])
def list_classes(db: Session = Depends(get_db), _=admin_only):
    """Retourne toutes les classes enregistrées."""
    classes = db.query(Classe).all()
    return classes


@router.post("/classes", response_model=ClasseResponse, status_code=status.HTTP_201_CREATED)
def create_classe(data: ClasseCreate, db: Session = Depends(get_db), _=admin_only):
    """Crée une nouvelle classe."""
    classe = Classe(**data.model_dump())

    try:
        db.add(classe)
        db.commit()
        db.refresh(classe)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Impossible de créer la classe"
        )

    return classe


@router.put("/classes/{classe_id}", response_model=ClasseResponse)
def update_classe(classe_id: int, data: ClasseUpdate, db: Session = Depends(get_db), _=admin_only):
    """Modifie les champs d'une classe existante (mise à jour partielle)."""

    classe = db.query(Classe).filter(Classe.id == classe_id).first()

    if classe is None:
        raise HTTPException(status_code=404, detail="Classe introuvable")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(classe, field, value)

    try:
        db.commit()
        db.refresh(classe)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Erreur lors de la modification de la classe"
        )

    return classe


@router.delete("/classes/{classe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_classe(classe_id: int, db: Session = Depends(get_db), _=admin_only):
    """Supprime une classe."""

    classe = db.query(Classe).filter(Classe.id == classe_id).first()

    if classe is None:
        raise HTTPException(status_code=404, detail="Classe introuvable")

    try:
        db.delete(classe)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Impossible de supprimer la classe (des étudiants ou données y sont rattachés)"
        )


# ─────────────────────────────────────────────
# MATIÈRES
# ─────────────────────────────────────────────

@router.get("/matieres", response_model=list[MatiereResponse])
def list_matieres(db: Session = Depends(get_db), _=admin_only):
    """Retourne toutes les matières."""
    matieres = db.query(Matiere).all()
    return matieres


@router.post("/matieres", response_model=MatiereResponse, status_code=status.HTTP_201_CREATED)
def create_matiere(data: MatiereCreate, db: Session = Depends(get_db), _=admin_only):
    """Crée une nouvelle matière."""

    matiere = Matiere(**data.model_dump())

    try:
        db.add(matiere)
        db.commit()
        db.refresh(matiere)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Impossible de créer la matière"
        )

    return matiere


@router.put("/matieres/{matiere_id}", response_model=MatiereResponse)
def update_matiere(matiere_id: int, data: MatiereUpdate, db: Session = Depends(get_db), _=admin_only):
    """Modifie partiellement une matière."""

    matiere = db.query(Matiere).filter(Matiere.id == matiere_id).first()

    if matiere is None:
        raise HTTPException(status_code=404, detail="Matière introuvable")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(matiere, field, value)

    try:
        db.commit()
        db.refresh(matiere)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Erreur lors de la modification de la matière"
        )

    return matiere


@router.delete("/matieres/{matiere_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_matiere(matiere_id: int, db: Session = Depends(get_db), _=admin_only):
    """Supprime une matière."""

    matiere = db.query(Matiere).filter(Matiere.id == matiere_id).first()

    if matiere is None:
        raise HTTPException(status_code=404, detail="Matière introuvable")

    try:
        db.delete(matiere)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Impossible de supprimer la matière (elle est utilisée ailleurs)"
        )


# Fin du fichier
