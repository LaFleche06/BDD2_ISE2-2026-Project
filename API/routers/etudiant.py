"""
Router Étudiant

Endpoints :
    GET /etudiant/profil        → informations personnelles + classe
    GET /etudiant/notes         → toutes ses notes avec détail matière
    GET /etudiant/dashboard     → vue complète :
                                    moyenne pondérée calculée à la volée,
                                    rang et décision depuis le dernier résultat officiel,
                                    notes détaillées par matière

Accès : rôle "etudiant".
"""

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from database.session import get_db
from models.models import Etudiant, Note, Resultat, Utilisateur
from schemas.schemas import (
    EtudiantResponse,
    NoteResponse,
    DashboardEtudiant,
    NoteDetaillee,
)
from core.dependencies import require_role

router = APIRouter(prefix="/etudiant", tags=["Étudiant"])
etudiant_only = require_role("etudiant")


# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────

def _get_etudiant(current_user: Utilisateur, db: Session) -> Etudiant:
    """Récupère le profil Etudiant lié à l'utilisateur connecté."""
    etudiant = db.query(Etudiant).filter(
        Etudiant.utilisateur_id == current_user.id
    ).first()
    if etudiant is None:
        raise HTTPException(status_code=404, detail="Profil étudiant introuvable")
    return etudiant


# ─────────────────────────────────────────────
# PROFIL
# ─────────────────────────────────────────────

@router.get("/profil", response_model=EtudiantResponse)
def mon_profil(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(etudiant_only),
):
    """Retourne les informations personnelles de l'étudiant connecté."""
    return _get_etudiant(current_user, db)


# ─────────────────────────────────────────────
# NOTES
# ─────────────────────────────────────────────

@router.get("/notes", response_model=list[NoteResponse])
def mes_notes(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(etudiant_only),
):
    """Retourne toutes les notes de l'étudiant connecté avec le détail des matières."""
    etudiant = _get_etudiant(current_user, db)
    return db.query(Note).filter(
        Note.etudiant_id == etudiant.matricule
    ).all()


# ─────────────────────────────────────────────
# DASHBOARD COMPLET
# ─────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardEtudiant)
def mon_dashboard(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(etudiant_only),
):
    """
    Tableau de bord complet de l'étudiant.

    - Notes détaillées par matière (avec coefficient)
    - Moyenne pondérée calculée à la volée (toujours à jour)
    - Rang et décision issus du dernier résultat officiel sauvegardé
      (None si aucune sauvegarde n'a encore été faite par l'admin)
    """
    etudiant = _get_etudiant(current_user, db)

    # Notes avec détail matière
    rows = db.execute(
        text("""
            SELECT
                m.nom         AS matiere,
                m.coefficient AS coefficient,
                n.valeur      AS valeur
            FROM note n
            JOIN matiere m ON m.id = n.matiere_id
            WHERE n.etudiant_id = :matricule
            ORDER BY m.nom
        """),
        {"matricule": etudiant.matricule},
    ).fetchall()

    notes_detaillees = [
        NoteDetaillee(
            matiere     = row[0],
            coefficient = Decimal(str(row[1])),
            valeur      = Decimal(str(row[2])),
        )
        for row in rows
    ]

    # Moyenne pondérée calculée en Python (pas de ROUND SQL pour la précision)
    if notes_detaillees:
        total_pondere = sum(n.valeur * n.coefficient for n in notes_detaillees)
        total_coeff   = sum(n.coefficient for n in notes_detaillees)
        moyenne = round(total_pondere / total_coeff, 2) if total_coeff else None
    else:
        moyenne = None

    # Rang et décision depuis le dernier résultat officiel
    resultat = (
        db.query(Resultat)
        .filter(Resultat.etudiant_id == etudiant.matricule)
        .order_by(Resultat.id.desc())
        .first()
    )

    return DashboardEtudiant(
        matricule        = etudiant.matricule,
        nom              = etudiant.nom,
        prenom           = etudiant.prenom,
        classe           = etudiant.classe.libelle,
        annee_scolaire   = etudiant.classe.annee_scolaire,
        moyenne_generale = moyenne,
        rang             = resultat.rang      if resultat else None,
        decision         = resultat.decision  if resultat else None,
        notes            = notes_detaillees,
    )