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

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from sqlalchemy import text



from database.session import get_db

from models.models import Etudiant, Note, Resultat, Utilisateur, Matiere, Intervention

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

# DASHBOARD

# ─────────────────────────────────────────────



@router.get("/dashboard", response_model=DashboardEtudiant)

def dashboard(

    db: Session = Depends(get_db),

    current_user: Utilisateur = Depends(etudiant_only),

):

    """Retourne le tableau de bord complet de l'étudiant avec calcul des moyennes et rangs."""

    etudiant = _get_etudiant(current_user, db)



    # ── Notes par matière via les interventions de la classe ──────────────

    # On utilise le nom de table ORM réel : 'intervention'

    rows = db.execute(

        text("""

            SELECT

                m.nom         AS matiere,

                m.coefficient AS coefficient,

                n.valeur      AS valeur,

                (SELECT COUNT(n2.id)

                 FROM note n2

                 JOIN etudiant e2 ON n2.etudiant_id = e2.matricule

                 WHERE n2.matiere_id = m.id AND e2.classe_id = :classe_id) AS notes_saisies,

                (SELECT COUNT(e3.matricule)

                 FROM etudiant e3

                 WHERE e3.classe_id = :classe_id) AS total_etudiants,

                (SELECT COUNT(n3.id) + 1

                 FROM note n3

                 JOIN etudiant e4 ON n3.etudiant_id = e4.matricule

                 WHERE n3.matiere_id = m.id AND e4.classe_id = :classe_id

                 AND n3.valeur > n.valeur) AS rang_matiere

            FROM intervention i

            JOIN matiere m ON m.id = i.matiere_id

            LEFT JOIN note n ON n.matiere_id = m.id AND n.etudiant_id = :matricule

            WHERE i.classe_id = :classe_id

            ORDER BY m.nom

        """),

        {"matricule": etudiant.matricule, "classe_id": etudiant.classe_id},

    ).fetchall()



    notes_detaillees = [

        NoteDetaillee(

            matiere         = row[0],

            coefficient     = Decimal(str(row[1])),

            valeur          = Decimal(str(row[2])) if row[2] is not None else None,

            notes_saisies   = row[3],

            total_etudiants = row[4],

            rang_matiere    = row[5] if row[2] is not None else None,

        )

        for row in rows

    ]



    # ── Moyenne pondérée calculée en Python ──────────────────────────────

    notes_presentes = [n for n in notes_detaillees if n.valeur is not None]

    if notes_presentes:

        total_pondere = sum(n.valeur * n.coefficient for n in notes_presentes)

        total_coeff   = sum(n.coefficient for n in notes_presentes)

        moyenne = round(total_pondere / total_coeff, 2) if total_coeff else None

    else:

        moyenne = None



    # ── Rang officiel (dernier résultat sauvegardé) ───────────────────────

    resultat = (

        db.query(Resultat)

        .filter(Resultat.etudiant_id == etudiant.matricule)

        .order_by(Resultat.id.desc())

        .first()

    )



    rang_calcule = None

    if not resultat:

        # Rang provisoire calculé depuis les notes actuelles

        prov_rows = db.execute(

            text("""

                SELECT

                    e.matricule,

                    RANK() OVER (

                        ORDER BY (

                            CASE WHEN SUM(CASE WHEN n.valeur IS NOT NULL THEN m.coefficient ELSE 0 END) > 0

                            THEN CAST(SUM(CASE WHEN n.valeur IS NOT NULL THEN n.valeur * m.coefficient ELSE 0 END) AS REAL) /

                                 CAST(SUM(CASE WHEN n.valeur IS NOT NULL THEN m.coefficient ELSE 0 END) AS REAL)

                            ELSE NULL END

                        ) DESC

                    ) AS rang

                FROM etudiant e

                JOIN intervention i ON i.classe_id = e.classe_id

                JOIN matiere m ON m.id = i.matiere_id

                LEFT JOIN note n ON n.etudiant_id = e.matricule AND n.matiere_id = m.id

                WHERE e.classe_id = :classe_id

                GROUP BY e.matricule

            """),

            {"classe_id": etudiant.classe_id},

        ).fetchall()



        for r in prov_rows:

            if r[0] == etudiant.matricule:

                rang_calcule = r[1]
                break

    total_etudiants = db.query(Etudiant).filter(Etudiant.classe_id == etudiant.classe_id).count()
    return DashboardEtudiant(
        matricule        = etudiant.matricule,
        nom              = etudiant.nom,
        prenom           = etudiant.prenom,
        classe           = etudiant.classe.libelle,
        annee_scolaire   = etudiant.classe.annee_scolaire,
        moyenne_generale = moyenne,
        rang             = resultat.rang      if resultat else rang_calcule,
        total_etudiants  = total_etudiants,
        decision         = resultat.decision  if resultat else None,
        notes            = notes_detaillees,
    )