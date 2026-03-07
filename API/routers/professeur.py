"""
Router Professeur

Endpoints :
    GET    /prof/interventions                  → ses affectations (matière → classe)
    GET    /prof/classes/{classe_id}/etudiants  → étudiants d'une de ses classes
    GET    /prof/notes                          → toutes ses notes saisies
    POST   /prof/notes                          → saisir une note
    PUT    /prof/notes/{note_id}                → modifier une de ses notes
    DELETE /prof/notes/{note_id}                → supprimer une de ses notes
    GET    /prof/classes/{classe_id}/moyennes   → moyennes pondérées + classement provisoire

Accès : rôle "prof". L'admin peut aussi accéder (require_role("prof", "admin")).
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from database.session import get_db
from models.models import Note, Professeur, Intervention, Etudiant, Utilisateur
from schemas.schemas import NoteCreate, NoteUpdate, NoteResponse, InterventionResponse
from core.dependencies import require_role

router = APIRouter(prefix="/prof", tags=["Professeur"])
prof_ou_admin = require_role("prof", "admin")


# ─────────────────────────────────────────────
# HELPERS INTERNES
# ─────────────────────────────────────────────

def _get_professeur(current_user: Utilisateur, db: Session) -> Professeur:
    """Récupère le profil Professeur lié à l'utilisateur connecté."""
    prof = db.query(Professeur).filter(
        Professeur.utilisateur_id == current_user.id
    ).first()
    if prof is None:
        raise HTTPException(status_code=404, detail="Profil professeur introuvable")
    return prof


def _verifier_affectation(prof: Professeur, matiere_id: int,
                           db: Session, current_user: Utilisateur) -> None:
    """Vérifie que le prof est affecté à cette matière. Admin bypass."""
    if current_user.role == "admin":
        return
    ok = db.query(Intervention).filter(
        Intervention.professeur_id == prof.id,
        Intervention.matiere_id    == matiere_id,
    ).first()
    if ok is None:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas affecté à cette matière")


def _verifier_classe(prof: Professeur, classe_id: int,
                     db: Session, current_user: Utilisateur) -> None:
    """Vérifie que le prof enseigne dans cette classe. Admin bypass."""
    if current_user.role == "admin":
        return
    ok = db.query(Intervention).filter(
        Intervention.professeur_id == prof.id,
        Intervention.classe_id     == classe_id,
    ).first()
    if ok is None:
        raise HTTPException(status_code=403, detail="Vous n'enseignez pas dans cette classe")


# ─────────────────────────────────────────────
# AFFECTATIONS
# ─────────────────────────────────────────────

@router.get("/interventions", response_model=list[InterventionResponse])
def mes_interventions(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(prof_ou_admin),
):
    """Retourne les affectations (matière → classe) du professeur connecté."""
    prof = _get_professeur(current_user, db)
    return db.query(Intervention).filter(
        Intervention.professeur_id == prof.id
    ).all()


# ─────────────────────────────────────────────
# ÉTUDIANTS D'UNE CLASSE
# ─────────────────────────────────────────────

@router.get("/classes/{classe_id}/etudiants")
def etudiants_de_ma_classe(
    classe_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(prof_ou_admin),
):
    """
    Liste les étudiants d'une classe dans laquelle le prof enseigne.
    Utile pour choisir l'étudiant lors de la saisie d'une note.
    """
    prof = _get_professeur(current_user, db)
    _verifier_classe(prof, classe_id, db, current_user)

    return [
        {"matricule": e.matricule, "nom": e.nom, "prenom": e.prenom}
        for e in db.query(Etudiant)
                   .filter(Etudiant.classe_id == classe_id)
                   .order_by(Etudiant.nom)
                   .all()
    ]


# ─────────────────────────────────────────────
# NOTES — LECTURE
# ─────────────────────────────────────────────

@router.get("/notes", response_model=list[NoteResponse])
def mes_notes(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(prof_ou_admin),
):
    """Retourne toutes les notes saisies par le professeur connecté."""
    prof = _get_professeur(current_user, db)
    return db.query(Note).filter(Note.professeur_id == prof.id).all()


# ─────────────────────────────────────────────
# NOTES — SAISIE
# ─────────────────────────────────────────────

@router.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def saisir_note(
    data: NoteCreate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(prof_ou_admin),
):
    """
    Saisit une note pour un étudiant.
    Règles :
    - Le prof doit être affecté à la matière
    - Un étudiant ne peut avoir qu'une seule note par matière
    """
    prof = _get_professeur(current_user, db)
    _verifier_affectation(prof, data.matiere_id, db, current_user)

    existing = db.query(Note).filter(
        Note.etudiant_id == data.etudiant_id,
        Note.matiere_id  == data.matiere_id,
    ).first()
    if existing is not None:
        raise HTTPException(
            status_code=400,
            detail="Une note existe déjà pour cet étudiant dans cette matière",
        )

    note = Note(
        matiere_id    = data.matiere_id,
        professeur_id = prof.id,
        etudiant_id   = data.etudiant_id,
        valeur        = data.valeur,
        date_saisie   = data.date_saisie or datetime.now(timezone.utc),
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


# ─────────────────────────────────────────────
# NOTES — MODIFICATION
# ─────────────────────────────────────────────

@router.put("/notes/{note_id}", response_model=NoteResponse)
def modifier_note(
    note_id: int,
    data: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(prof_ou_admin),
):
    """
    Modifie une note existante.
    Un prof ne peut modifier que ses propres notes.
    L'admin peut tout modifier.
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    if note is None:
        raise HTTPException(status_code=404, detail="Note introuvable")

    if current_user.role != "admin":
        prof = _get_professeur(current_user, db)
        if note.professeur_id != prof.id:
            raise HTTPException(
                status_code=403,
                detail="Vous ne pouvez modifier que vos propres notes",
            )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(note, field, value)

    db.commit()
    db.refresh(note)
    return note


# ─────────────────────────────────────────────
# NOTES — SUPPRESSION
# ─────────────────────────────────────────────

@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(prof_ou_admin),
):
    """
    Supprime une note.
    Un prof ne peut supprimer que ses propres notes.
    L'admin peut tout supprimer.
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    if note is None:
        raise HTTPException(status_code=404, detail="Note introuvable")

    if current_user.role != "admin":
        prof = _get_professeur(current_user, db)
        if note.professeur_id != prof.id:
            raise HTTPException(
                status_code=403,
                detail="Vous ne pouvez supprimer que vos propres notes",
            )

    db.delete(note)
    db.commit()


# ─────────────────────────────────────────────
# MOYENNES PROVISOIRES PAR CLASSE
# ─────────────────────────────────────────────

@router.get("/classes/{classe_id}/moyennes")
def moyennes_de_ma_classe(
    classe_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(prof_ou_admin),
):
    """
    Classement provisoire des étudiants d'une classe (non sauvegardé).
    Différence avec /admin/classement : accessible au prof, limité à ses classes.
    """
    prof = _get_professeur(current_user, db)
    _verifier_classe(prof, classe_id, db, current_user)

    rows = db.execute(
        text("""
            SELECT
                e.matricule, e.nom, e.prenom,
                ROUND(
                    CAST(SUM(n.valeur * m.coefficient) AS REAL) /
                    NULLIF(CAST(SUM(m.coefficient) AS REAL), 0),
                2) AS moyenne,
                RANK() OVER (
                    ORDER BY (
                        CAST(SUM(n.valeur * m.coefficient) AS REAL) /
                        NULLIF(CAST(SUM(m.coefficient) AS REAL), 0)
                    ) DESC
                ) AS rang
            FROM etudiant e
            JOIN note n ON n.etudiant_id = e.matricule
            JOIN matiere m ON m.id = n.matiere_id
            WHERE e.classe_id = :classe_id
            GROUP BY e.matricule, e.nom, e.prenom
            ORDER BY rang
        """),
        {"classe_id": classe_id},
    ).fetchall()

    return [
        {
            "rang":     row[4],
            "matricule": row[0],
            "nom":      row[1],
            "prenom":   row[2],
            "moyenne":  float(row[3]) if row[3] is not None else None,
            "decision": "Admis" if row[3] is not None and float(row[3]) >= 10 else "Ajourné",
        }
        for row in rows
    ]