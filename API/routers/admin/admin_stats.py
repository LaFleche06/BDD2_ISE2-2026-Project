"""
Router Administrateur — Statistiques & Classements.

Ce module expose les endpoints réservés aux administrateurs permettant de :
- consulter les statistiques globales de l'établissement
- générer le classement d'une classe
- sauvegarder officiellement les résultats d'une classe
- consulter toutes les notes du système

Routes disponibles
------------------

GET  /admin/stats
    Tableau de bord global de l'établissement.

GET  /admin/classement/{classe_id}
    Génère dynamiquement le classement d'une classe.

POST /admin/classement/{classe_id}/sauvegarder
    Calcule et enregistre les résultats officiels d'une classe.

GET  /admin/notes
    Liste toutes les notes avec possibilité de filtrer par classe.

Accès
-----

Toutes les routes nécessitent le rôle **admin**.

Note technique — CAST(... AS REAL)
-----------------------------------
SQLite stocke les colonnes Numeric/Decimal comme des entiers si la valeur
ne contient pas de partie décimale explicite (ex: Decimal("2.00") → 2).
Sans CAST, la division entière tronque le résultat (14.666 → 14).
Le CAST force une division flottante, compatible avec SQL Server et SQLite.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from database.session import get_db
from models.models import (
    Etudiant,
    Professeur,
    Classe,
    Matiere,
    Note,
    Resultat
)
from schemas.schemas import NoteResponse,ResultatResponse
from core.dependencies import require_role


router = APIRouter(
    prefix="/admin",
    tags=["Admin — Statistiques et Classements"]
)

admin_only = Depends(require_role("admin"))

# ─────────────────────────────────────────────
# Fragment SQL réutilisé dans les 3 requêtes.
# CAST AS REAL garantit la division flottante sur SQLite ET SQL Server.
# ─────────────────────────────────────────────
_MOYENNE_SQL = """
    CAST(SUM(n.valeur * m.coefficient) AS REAL) /
    NULLIF(CAST(SUM(m.coefficient) AS REAL), 0)
"""


# ─────────────────────────────────────────────
# STATISTIQUES GLOBALES
# ─────────────────────────────────────────────

@router.get(
    "/stats",
    summary="Statistiques globales",
    description=(
        "Retourne les principaux indicateurs du système : "
        "nombre d'étudiants, professeurs, classes, matières, notes, "
        "ainsi que la moyenne générale et le taux de réussite."
    ),
)
def stats_globales(
    db: Session = Depends(get_db),
    _: object = admin_only,
):
    nb_etudiants   = db.query(func.count(Etudiant.matricule)).scalar() or 0
    nb_professeurs = db.query(func.count(Professeur.id)).scalar()      or 0
    nb_classes     = db.query(func.count(Classe.id)).scalar()          or 0
    nb_matieres    = db.query(func.count(Matiere.id)).scalar()         or 0
    nb_notes       = db.query(func.count(Note.id)).scalar()            or 0

    # Moyenne globale de l'établissement (pondérée)
    result = db.execute(
        text(f"""
            SELECT ROUND({_MOYENNE_SQL}, 2)
            FROM note n
            JOIN matiere m ON m.id = n.matiere_id
        """)
    ).fetchone()

    moyenne_etablissement = None
    if result and result[0] is not None:
        moyenne_etablissement = float(result[0])

    # Taux de réussite (étudiants avec moyenne >= 10)
    result_reussite = db.execute(
        text(f"""
            SELECT
                COUNT(*)                                          AS total,
                SUM(CASE WHEN moy >= 10 THEN 1 ELSE 0 END)       AS admis
            FROM (
                SELECT
                    e.matricule,
                    {_MOYENNE_SQL} AS moy
                FROM etudiant e
                JOIN note n ON n.etudiant_id = e.matricule
                JOIN matiere m ON m.id = n.matiere_id
                GROUP BY e.matricule
            ) AS moyennes
        """)
    ).fetchone()

    taux_reussite = None
    if result_reussite and result_reussite[0]:
        total = result_reussite[0]
        admis = result_reussite[1] or 0
        taux_reussite = round((admis / total) * 100, 1)

    return {
        "nb_etudiants":          nb_etudiants,
        "nb_professeurs":        nb_professeurs,
        "nb_classes":            nb_classes,
        "nb_matieres":           nb_matieres,
        "nb_notes":              nb_notes,
        "moyenne_etablissement": moyenne_etablissement,
        "taux_reussite_pct":     taux_reussite,
    }


@router.get(
    "/stats/classes/{classe_id}",
    summary="Statistiques d'une classe",
)
def stats_classe(
    classe_id: int,
    db: Session = Depends(get_db),
    _: object = admin_only,
):
    classe = db.query(Classe).filter(Classe.id == classe_id).first()
    if not classe:
        raise HTTPException(status_code=404, detail="Classe introuvable")

    result = db.execute(
        text(f"""
            SELECT
                COUNT(*)                                               AS nb_etudiants,
                SUM(CASE WHEN moy >= 10 THEN 1 ELSE 0 END)            AS nb_admis,
                SUM(CASE WHEN moy < 10  THEN 1 ELSE 0 END)            AS nb_ajournes,
                ROUND(AVG(moy), 2)                                     AS moyenne_classe,
                MAX(moy)                                               AS meilleure_moyenne,
                MIN(moy)                                               AS moins_bonne_moyenne
            FROM (
                SELECT
                    e.matricule,
                    {_MOYENNE_SQL} AS moy
                FROM etudiant e
                JOIN note n ON n.etudiant_id = e.matricule
                JOIN matiere m ON m.id = n.matiere_id
                WHERE e.classe_id = :classe_id
                GROUP BY e.matricule
            ) AS moyennes
        """),
        {"classe_id": classe_id},
    ).fetchone()

    nb_etudiants = result[0] or 0
    nb_admis     = result[1] or 0

    return {
        "classe_id":          classe_id,
        "classe":             classe.libelle,
        "annee_scolaire":     classe.annee_scolaire,
        "nb_etudiants":       nb_etudiants,
        "nb_admis":           nb_admis,
        "nb_ajournes":        result[2] or 0,
        "taux_reussite_pct":  round((nb_admis / nb_etudiants) * 100, 1) if nb_etudiants else None,
        "moyenne_classe":     float(result[3]) if result[3] is not None else None,
        "meilleure_moyenne":  float(result[4]) if result[4] is not None else None,
        "moins_bonne_moyenne": float(result[5]) if result[5] is not None else None,
    }
# ─────────────────────────────────────────────
# CLASSEMENT PAR CLASSE
# ─────────────────────────────────────────────

@router.get(
    "/classement/{classe_id}",
    summary="Classement d'une classe",
)
def classement_classe(
    classe_id: int,
    db: Session = Depends(get_db),
    _: object = admin_only,
):
    classe = db.query(Classe).filter(Classe.id == classe_id).first()
    if not classe:
        raise HTTPException(status_code=404, detail="Classe introuvable")

    result = db.execute(
        text(f"""
            SELECT
                e.matricule,
                e.nom,
                e.prenom,
                ROUND({_MOYENNE_SQL}, 2) AS moyenne,
                RANK() OVER (
                    ORDER BY ({_MOYENNE_SQL}) DESC
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

    classement = []
    for row in result:
        moyenne = float(row[3]) if row[3] is not None else None
        classement.append({
            "rang":      row[4],
            "matricule": row[0],
            "nom":       row[1],
            "prenom":    row[2],
            "moyenne":   moyenne,
            "decision":  "Admis" if moyenne is not None and moyenne >= 10 else "Ajourné",
        })

    return {
        "classe":        classe.libelle,
        "annee_scolaire": classe.annee_scolaire,
        "classement":    classement,
    }


# ─────────────────────────────────────────────
# SAUVEGARDE DES RÉSULTATS OFFICIELS
# ─────────────────────────────────────────────

@router.post(
    "/classement/{classe_id}/sauvegarder",
    status_code=status.HTTP_201_CREATED,
    summary="Sauvegarder les résultats officiels",
)
def sauvegarder_classement(
    classe_id: int,
    db: Session = Depends(get_db),
    _: object = admin_only,
):
    classe = db.query(Classe).filter(Classe.id == classe_id).first()
    if not classe:
        raise HTTPException(status_code=404, detail="Classe introuvable")

    result = db.execute(
        text(f"""
            SELECT
                e.matricule,
                ROUND({_MOYENNE_SQL}, 2) AS moyenne,
                RANK() OVER (
                    ORDER BY ({_MOYENNE_SQL}) DESC
                ) AS rang
            FROM etudiant e
            JOIN note n ON n.etudiant_id = e.matricule
            JOIN matiere m ON m.id = n.matiere_id
            WHERE e.classe_id = :classe_id
            GROUP BY e.matricule
        """),
        {"classe_id": classe_id},
    ).fetchall()

    if not result:
        raise HTTPException(
            status_code=400,
            detail="Aucune note trouvée pour cette classe",
        )

    # Supprime les anciens résultats (même classe + même année) avant réinsertion
    db.query(Resultat).filter(
        Resultat.classe_id == classe_id,
        Resultat.annee_scolaire == classe.annee_scolaire,
    ).delete(synchronize_session=False)

    for row in result:
        matricule, moyenne, rang = row
        moyenne = float(moyenne) if moyenne is not None else None
        db.add(Resultat(
            classe_id=classe_id,
            etudiant_id=matricule,
            moyenne_generale=moyenne,
            decision="Admis" if moyenne is not None and moyenne >= 10 else "Ajourné",
            annee_scolaire=classe.annee_scolaire,
            rang=rang,
        ))

    db.commit()
    return {"message": f"Résultats sauvegardés pour {len(result)} étudiant(s)"}

@router.get(
    "/resultats/{classe_id}",
    response_model=list[ResultatResponse],
    summary="Résultats officiels sauvegardés d'une classe",
)
def resultats_classe(
    classe_id: int,
    db: Session = Depends(get_db),
    _: object = admin_only,
):
    """
    Retourne les résultats officiels sauvegardés pour une classe.
    Vide si aucune sauvegarde n'a encore été faite.
    """
    classe = db.query(Classe).filter(Classe.id == classe_id).first()
    if not classe:
        raise HTTPException(status_code=404, detail="Classe introuvable")

    return (
        db.query(Resultat)
        .filter(Resultat.classe_id == classe_id)
        .order_by(Resultat.rang)
        .all()
    )

# ─────────────────────────────────────────────
# CONSULTATION GLOBALE DES NOTES
# ─────────────────────────────────────────────

@router.get(
    "/notes",
    response_model=list[NoteResponse],
    summary="Liste des notes",
)
def all_notes(
    classe_id: int | None = Query(None, description="Filtrer les notes par classe"),
    db: Session = Depends(get_db),
    _: object = admin_only,
):
    query = db.query(Note)

    if classe_id is not None:
        query = query.join(
            Etudiant, Note.etudiant_id == Etudiant.matricule
        ).filter(Etudiant.classe_id == classe_id)

    return query.all()